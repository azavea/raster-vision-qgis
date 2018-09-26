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
from PyQt5.QtWidgets import QTableWidgetItem

from qgis.core import Qgis

from .settings import Settings, StyleProfile
# from .viz_workflow import VizWorkflow, ExperimentLoadOptions
from .experiment_loader import (ExperimentLoader,
                                ExperimentLoadOptions,
                                SceneLoadOptions,
                                LoadContext)
from .log import Log

import rastervision as rv
from rastervision.utils.files import load_json_config
from rastervision.protos.experiment_pb2 import ExperimentConfig as ExperimentConfigMsg
from rastervision.filesystem.s3_filesystem import S3FileSystem


FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'experiment_dialog_base.ui'))


class ExperimentDialog(QtWidgets.QDialog, FORM_CLASS):
    def __init__(self, parent=None):
        """Constructor."""

        super(ExperimentDialog, self).__init__(parent)
        self.setupUi(self)

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

    def set_list_items(self, scene_ids):
        table.clear()
        table.setRowCount(len(rows))
        for i, row in enumerate(rows):
            for j, column in enumerate(row):
                if column == 'x':
                    item = QTableWidgetItem()
                    item.setFlags(QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled)
                    item.setCheckState(QtCore.Qt.Unchecked)
                else:
                    item = QTableWidgetItem(column)

                item.setTextAlignment(QtCore.Qt.AlignHCenter)
                table.setItem(i, j, item)

    def load_experiment_clicked(self):
        experiment_uri = self.experiment_uri_line_edit.text()
        Log.log_info("Loading experiment at {}".format(experiment_uri))
        msg = load_json_config(experiment_uri, ExperimentConfigMsg())
        experiment = rv.ExperimentConfig.from_proto(msg)
        ds = experiment.dataset

        for scene in ds.train_scenes:
            item = QtWidgets.QListWidgetItem(scene.id, self.train_scene_list)
            item.setFlags(QtCore.Qt.ItemIsUserCheckable |
                          QtCore.Qt.ItemIsEnabled)
            item.setCheckState(QtCore.Qt.Checked)
            self.train_scene_list.addItem(item)

        for scene in ds.validation_scenes:
            item = QtWidgets.QListWidgetItem(scene.id, self.validation_scene_list)
            item.setFlags(QtCore.Qt.ItemIsUserCheckable |
                          QtCore.Qt.ItemIsEnabled)
            item.setCheckState(QtCore.Qt.Checked)
            self.validation_scene_list.addItem(item)

        for scene in ds.test_scenes:
            item = QtWidgets.QListWidgetItem(scene.id, self.test_scene_list)
            item.setFlags(QtCore.Qt.ItemIsUserCheckable |
                          QtCore.Qt.ItemIsEnabled)
            item.setCheckState(QtCore.Qt.Checked)
            self.test_scene_list.addItem(item)


class ExperimentDialogController(object):
    def __init__(self, iface):
        self.dlg = ExperimentDialog()
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

        # options = settings.get_experiment_load_options()
        # self.dlg.training_scenes_checkbox.setChecked(options.training_scenes)
        # self.dlg.training_labels_checkbox.setChecked(options.training_labels)
        # self.dlg.validation_scenes_checkbox.setChecked(options.validation_scenes)
        # self.dlg.validation_labels_checkbox.setChecked(options.validation_labels)
        # self.dlg.validation_predictions_checkbox.setChecked(options.validation_predictions)
        # self.dlg.prediction_scenes_checkbox.setChecked(options.prediction_scenes)
        # self.dlg.predictions_checkbox.setChecked(options.predictions)

        result = self.dlg.exec_()

        if result:
            style_profile_index = self.dlg.style_profile_combobox.currentIndex()
            settings.set_experiment_profile(profile_names[style_profile_index])

            experiment_uri = self.dlg.experiment_uri_line_edit.text()
            settings.set_experiment_uri(experiment_uri)

            style_profile = None
            if not style_profile_index == 0:
                style_profile = profiles[style_profile_index]

            msg = load_json_config(experiment_uri, ExperimentConfigMsg())
            experiment = rv.ExperimentConfig.from_proto(msg)
            Log.log_info("Loading experiment at {}".format(experiment_uri))

            load_image = self.dlg.images_checkbox.checkState()
            load_ground_truth = self.dlg.ground_truth_checkbox.checkState()
            load_predictions = self.dlg.predictions_checkbox.checkState()
            load_aoi = self.dlg.aoi_checkbox.checkState()

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

            ctx = LoadContext(experiment=experiment,
                              iface=self.iface,
                              style_profile=style_profile,
                              working_dir=settings.get_working_dir())

            # Set AWS Profile if we have one
            profile = settings.get_aws_profile()
            if profile:
                S3FileSystem.set_profile(profile)

            Log.log_info("{}".format(profile))
            errors = ExperimentLoader.load(experiment, opts, ctx)

            if errors:
                msg = "Some Files Not Loaded. Check Logs for details."
                widget = self.iface.messageBar().createMessage("Raster Vision", msg)
                # button = QtWidgets.QPushButton(widget)
                # button.setText("View Logs.")
                # button.pressed.connect(self.showLogs)
                # widget.layout().addWidget(button)
                self.iface.messageBar().pushWidget(widget, Qgis.Warning)
