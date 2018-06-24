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

from .experiment_info_dialog import ExperimentInfoDialog
from .settings import Settings, StyleProfile
from .viz_workflow import VizWorkflow


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


            v = VizWorkflow(self.iface,
                            rv_root,
                            workflow_uri,
                            settings.get_working_dir(),
                            settings.get_aws_profile(),
                            style_profile)

            # Load RV Layers
            v.show()
