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
from PyQt5 import QtWidgets

from qgis.core import Qgis

from .experiment_info_dialog import ExperimentInfoDialog
from .settings import Settings, StyleProfile
from .viz_workflow import VizWorkflow, ExperimentLoadOptions


FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'experiment_dialog_base.ui'))


class ExperimentDialog(QtWidgets.QDialog, FORM_CLASS):
    def __init__(self, parent=None):
        """Constructor."""

        super(ExperimentDialog, self).__init__(parent)
        self.setupUi(self)

        self.info_button.clicked.connect(self.show_info)

        self.info_dialog = ExperimentInfoDialog()

    def  show_info(self):
        self.info_dialog.show()
        self.info_dialog.exec_()


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

        self.dlg.rv_root_line_edit.setText(settings.get_rv_root())
        self.dlg.workflow_uri_line_edit.setText(settings.get_workflow_uri())

        profiles = settings.get_style_profiles()
        profiles.insert(0, StyleProfile.EMPTY())
        profile_names = list(map(lambda p: p.name, profiles))
        self.dlg.style_profile_combobox.addItems(profile_names)
        settings_profile = settings.get_experiment_profile()
        if settings_profile in profile_names:
            self.dlg.style_profile_combobox.setCurrentIndex(profile_names.index(settings_profile))
        else:
            self.dlg.style_profile_combobox.setCurrentIndex(0)

        options = settings.get_experiment_load_options()
        self.dlg.training_scenes_checkbox.setChecked(options.training_scenes)
        self.dlg.training_labels_checkbox.setChecked(options.training_labels)
        self.dlg.validation_scenes_checkbox.setChecked(options.validation_scenes)
        self.dlg.validation_labels_checkbox.setChecked(options.validation_labels)
        self.dlg.validation_predictions_checkbox.setChecked(options.validation_predictions)
        self.dlg.prediction_scenes_checkbox.setChecked(options.prediction_scenes)
        self.dlg.predictions_checkbox.setChecked(options.predictions)

        result = self.dlg.exec_()

        if result:
            style_profile_index = self.dlg.style_profile_combobox.currentIndex()
            settings.set_experiment_profile(profile_names[style_profile_index])

            rv_root = self.dlg.rv_root_line_edit.text()
            settings.set_rv_root(rv_root)

            workflow_uri = self.dlg.workflow_uri_line_edit.text()
            settings.set_workflow_uri(workflow_uri)

            style_profile = None
            if not style_profile_index == 0:
                style_profile = profiles[style_profile_index]

            options = ExperimentLoadOptions(self.dlg.training_scenes_checkbox.isChecked(),
                                            self.dlg.training_labels_checkbox.isChecked(),
                                            self.dlg.validation_scenes_checkbox.isChecked(),
                                            self.dlg.validation_labels_checkbox.isChecked(),
                                            self.dlg.validation_predictions_checkbox.isChecked(),
                                            self.dlg.prediction_scenes_checkbox.isChecked(),
                                            self.dlg.predictions_checkbox.isChecked())
            settings.set_experiment_load_options(options)


            v = VizWorkflow(self.iface,
                            rv_root,
                            workflow_uri,
                            settings.get_working_dir(),
                            settings.get_aws_profile(),
                            style_profile,
                            options)

            # Load RV Layers
            errors = v.show()

            if errors:
                msg = "Some Files Not Loaded. Check Logs for details."
                widget = self.iface.messageBar().createMessage("Raster Vision", msg)
                # button = QtWidgets.QPushButton(widget)
                # button.setText("View Logs.")
                # button.pressed.connect(self.showLogs)
                # widget.layout().addWidget(button)
                self.iface.messageBar().pushWidget(widget, Qgis.Warning)
