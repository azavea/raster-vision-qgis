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

from .settings import Settings, InfoUrls

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'predict_info_dialog_base.ui'))


class PredictInfoDialog(QtWidgets.QDialog, FORM_CLASS):
    def __init__(self, parent=None):
        super(PredictInfoDialog, self).__init__(parent)
        self.setupUi(self)

        self.more_info_label.setOpenExternalLinks(True)
        self.more_info_label.setText("<a href=\"{}\">More Information</a>".format(InfoUrls().predict))
