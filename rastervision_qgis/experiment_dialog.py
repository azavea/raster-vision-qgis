# -*- coding: utf-8 -*-
"""
/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

import os

from PyQt5 import uic
from PyQt5 import (QtWidgets, QtCore)
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtCore import Qt

from qgis.core import (Qgis, QgsProject)

from .settings import Settings, StyleProfile
from .experiment_loader import (ExperimentLoader,
                                ExperimentLoadOptions,
                                SceneLoadOptions,
                                LoadContext)
from .log import Log

import rastervision as rv
from rastervision.utils.files import load_json_config
from rastervision.filesystem import NotReadableError
from rastervision.protos.experiment_pb2 import ExperimentConfig as ExperimentConfigMsg
from rastervision.filesystem import ProtobufParseException
from rastervision.filesystem.s3_filesystem import S3FileSystem


FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'experiment_dialog_base.ui'))


class ExperimentDialog(QtWidgets.QDialog, FORM_CLASS):
    def __init__(self, iface, parent=None):
        """Constructor."""

        super(ExperimentDialog, self).__init__(parent)
        self.setupUi(self)

        self.iface = iface

        self.load_button.clicked.connect(self.load_experiment_clicked)

        def select_all(check_state_fn, target_list):
            def f():
                state = QtCore.Qt.Unchecked
                if check_state_fn():
                    state = QtCore.Qt.Checked

                for n in range(0, target_list.count()):
                    item = target_list.item(n).setCheckState(state)
            return f

        self.train_scenes_all_checkbox \
            .clicked \
            .connect(select_all(self.train_scenes_all_checkbox.checkState,
                                self.train_scene_list))

        self.validation_scenes_all_checkbox \
            .clicked \
            .connect(select_all(self.validation_scenes_all_checkbox.checkState,
                                self.validation_scene_list))

        self.test_scenes_all_checkbox \
            .clicked \
            .connect(select_all(self.test_scenes_all_checkbox.checkState,
                                self.test_scene_list))

    def load_experiment_clicked(self):
        experiment_uri = self.experiment_uri_line_edit.text()
        Log.log_info("Loading experiment at {}".format(experiment_uri))
        QtWidgets.QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            msg = load_json_config(experiment_uri, ExperimentConfigMsg())
        except (NotReadableError, ProtobufParseException) as e:
            reply = QMessageBox.warning(self.iface.mainWindow(), 'Error',
                                        'Unable to read experiment file. See log more details.', QMessageBox.Ok)
            Log.log_warning('Unable to read experiment file: {}'.format(experiment_uri))
            Log.log_exception(e)
            return
        finally:
            QtWidgets.QApplication.restoreOverrideCursor()

        experiment = rv.ExperimentConfig.from_proto(msg)
        self.experiment = experiment
        ds = experiment.dataset

        self.train_scene_list.clear()
        for scene in ds.train_scenes:
            item = QtWidgets.QListWidgetItem(scene.id, self.train_scene_list)
            item.setFlags(QtCore.Qt.ItemIsUserCheckable |
                          QtCore.Qt.ItemIsEnabled)
            item.setCheckState(QtCore.Qt.Checked)
            self.train_scene_list.addItem(item)

        self.validation_scene_list.clear()
        for scene in ds.validation_scenes:
            item = QtWidgets.QListWidgetItem(scene.id, self.validation_scene_list)
            item.setFlags(QtCore.Qt.ItemIsUserCheckable |
                          QtCore.Qt.ItemIsEnabled)
            item.setCheckState(QtCore.Qt.Checked)
            self.validation_scene_list.addItem(item)

        self.test_scene_list.clear()
        for scene in ds.test_scenes:
            item = QtWidgets.QListWidgetItem(scene.id, self.test_scene_list)
            item.setFlags(QtCore.Qt.ItemIsUserCheckable |
                          QtCore.Qt.ItemIsEnabled)
            item.setCheckState(QtCore.Qt.Checked)
            self.test_scene_list.addItem(item)


class ExperimentDialogController(object):
    def __init__(self, iface):
        self.dlg = ExperimentDialog(iface)
        self.iface = iface

    def showLogs(self):
        # TODO
        pass

    def run(self):
        self.dlg.show()

        settings = Settings()

        self.dlg.experiment_uri_line_edit.setText(settings.get_experiment_uri())

        profiles = settings.get_style_profiles()
        profiles.insert(0, StyleProfile.EMPTY())
        profile_names = list(map(lambda p: p.name, profiles))
        self.dlg.style_profile_combobox.clear()
        self.dlg.style_profile_combobox.addItems(profile_names)
        settings_profile = settings.get_experiment_profile()
        if settings_profile in profile_names:
            self.dlg.style_profile_combobox.setCurrentIndex(profile_names.index(settings_profile))
        else:
            self.dlg.style_profile_combobox.setCurrentIndex(0)

        result = self.dlg.exec_()

        if result:
            style_profile_index = self.dlg.style_profile_combobox.currentIndex()
            settings.set_experiment_profile(profile_names[style_profile_index])

            experiment_uri = self.dlg.experiment_uri_line_edit.text()
            settings.set_experiment_uri(experiment_uri)

            style_profile = None
            if not style_profile_index == 0:
                style_profile = profiles[style_profile_index]

            experiment = self.dlg.experiment

            load_image = self.dlg.images_checkbox.checkState()
            load_ground_truth = self.dlg.ground_truth_checkbox.checkState()
            load_predictions = self.dlg.predictions_checkbox.checkState()
            load_aoi = self.dlg.aoi_checkbox.checkState()

            # Check that we really want to clear the project if there
            # are existing layers.
            project = QgsProject.instance()
            layers = list(project.mapLayers().values())

            if len(layers) > 0:
                reply = QMessageBox.question(self.iface.mainWindow(), 'Continue?',
                                             ('There are existing layers that will be cleared '
                                              'from this project. Continue?'), QMessageBox.Yes, QMessageBox.No)
                if reply == QMessageBox.No:
                    return

            train_scenes = []
            for n in range(0, self.dlg.train_scene_list.count()):
                item = self.dlg.train_scene_list.item(n)
                if item.checkState():
                    train_scenes.append(SceneLoadOptions(item.text(),
                                                         load_image,
                                                         load_ground_truth,
                                                         False,
                                                         load_aoi))

            validation_scenes = []
            for n in range(0, self.dlg.validation_scene_list.count()):
                item = self.dlg.validation_scene_list.item(n)
                if item.checkState():
                    validation_scenes.append(SceneLoadOptions(item.text(),
                                                              load_image,
                                                              load_ground_truth,
                                                              load_predictions,
                                                              load_aoi))

            test_scenes = []
            for n in range(0, self.dlg.test_scene_list.count()):
                item = self.dlg.test_scene_list.item(n)
                if item.checkState():
                    test_scenes.append(SceneLoadOptions(item.text(),
                                                        load_image,
                                                        False,
                                                        load_predictions,
                                                        False))

            opts = ExperimentLoadOptions(
                train_scenes=train_scenes,
                validation_scenes=validation_scenes,
                test_scenes=test_scenes
            )

            ctx = LoadContext(task=experiment.task,
                              iface=self.iface,
                              style_profile=style_profile,
                              working_dir=settings.get_working_dir())

            errors = ExperimentLoader.load(experiment, opts, ctx)

            if errors:
                msg = "Some Files Not Loaded. Check Logs for details."
                widget = self.iface.messageBar().createMessage("Raster Vision", msg)
                self.iface.messageBar().pushWidget(widget, Qgis.Warning)
