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

from .predict_info_dialog import PredictInfoDialog
from .settings import Settings, StyleProfile
from .viz_workflow import VizWorkflow


FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'predict_dialog_base.ui'))


class PredictDialog(QtWidgets.QDialog, FORM_CLASS):
    def __init__(self, parent=None):
        """Constructor."""

        super(PredictDialog, self).__init__(parent)
        self.setupUi(self)

        self.info_button.clicked.connect(self.show_info)

        self.info_dialog = PredictInfoDialog()

    def  show_info(self):
        self.info_dialog.show()
        self.info_dialog.exec_()


class PredictDialogController(object):
    def __init__(self):
        self.dlg = PredictDialog()

    def run(self):
        self.dlg.show()

        settings = Settings()

        self.dlg.model_file_edit.setText(settings.get_model_file())

        profiles = settings.get_style_profiles()
        profiles.insert(0, StyleProfile.EMPTY())
        profile_names = list(map(lambda p: p.name, profiles))
        self.dlg.style_profile_combobox.addItems(profile_names)
        settings_profile = settings.get_predict_profile()
        if settings_profile in profile_names:
            self.dlg.style_profile_combobox.setCurrentIndex(profile_names.index(settings_profile))
        else:
            self.dlg.style_profile_combobox.setCurrentIndex(0)

        result = self.dlg.exec_()

        if result:
            model_file = self.dlg.model_file_edit.text()
            settings.set_get_model_file(model_file)

            # TODO: Execute
