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

from .settings import Settings

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'config_dialog_base.ui'))


class ConfigDialog(QtWidgets.QDialog, FORM_CLASS):
    def __init__(self, parent=None):
        """Constructor."""
        super(ConfigDialog, self).__init__(parent)
        self.setupUi(self)

        self.working_dir_file_select_button.clicked.connect(self.select_working_dir)

    def select_working_dir(self):
        path = QtWidgets.QFileDialog.getExistingDirectory()
        if path:
            self.working_dir_edit.setText(path)


class ConfigDialogController(object):
    def __init__(self):
        self.dlg = ConfigDialog()

    def run(self):
        settings = Settings()

        self.dlg.show()

        self.dlg.working_dir_edit.setText(settings.get_working_dir())
        self.dlg.aws_profile_edit.setText(settings.get_aws_profile())

        # Run the dialog event loop
        result = self.dlg.exec_()

        if result:
            settings.set_working_dir(self.dlg.working_dir_edit.text())

            aws_profile = self.dlg.aws_profile_edit.text()
            settings.set_aws_profile(aws_profile)
