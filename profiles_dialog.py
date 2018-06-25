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

from .settings import Settings, StyleProfile

from .profiles_info_dialog import ProfilesInfoDialog
from .profiles_add_dialog import  ProfilesAddDialog

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'profiles_dialog_base.ui'))


class ProfilesDialog(QtWidgets.QDialog, FORM_CLASS):
    def __init__(self, parent=None):
        """Constructor."""
        super(ProfilesDialog, self).__init__(parent)

        self.setupUi(self)

        self.info_button.clicked.connect(self.show_info)
        self.info_dialog = ProfilesInfoDialog()

        self.add_profile_button.clicked.connect(self.add_profile_clicked)
        self.profiles_combobox.currentIndexChanged.connect(self.profiles_index_changed)

        def connect_file_button(button, edit):
            def set_edit():
                path = QtWidgets.QFileDialog.getOpenFileName()
                if path:
                    edit.setText(path[0])
            button.clicked.connect(set_edit)

        connect_file_button(self.training_scenes_button,
                            self.training_scenes_edit.setText)
        connect_file_button(self.training_labels_button,
                            self.training_labels_edit)
        connect_file_button(self.validation_scenes_button,
                            self.validation_scenes_edit)
        connect_file_button(self.validation_labels_button,
                            self.validation_labels_edit)
        connect_file_button(self.validation_predictions_button,
                            self.validation_predictions_edit)
        connect_file_button(self.prediction_scenes_button,
                            self.prediction_scenes_edit)
        connect_file_button(self.predictions_button,
                            self.predictions_edit)

    def show_info(self):
        self.info_dialog.show()
        self.info_dialog.exec_()

    def add_profile_clicked(self):
        # Run add profile dialog, set up new profile
        add_dlg = ProfilesAddDialog()

        add_dlg.show()

        result = add_dlg.exec_()

        if result:
            profile = StyleProfile(add_dlg.profile_name_edit.text())
            self.add_profile_callback(profile)

    def profiles_index_changed(self, i):
        self.profile_changed_callback(i)

    def set_add_profile_callback(self, callback):
        self.add_profile_callback = callback

    def set_profile_changed_callback(self, callback):
        self.profile_changed_callback = callback


class ProfilesDialogController(object):
    def __init__(self):
        self.dlg = ProfilesDialog()
        self.dlg.set_add_profile_callback(self.add_profile_callback)
        self.dlg.set_profile_changed_callback(self.profile_changed_callback)

    def add_profile_callback(self, profile):
        """
        Adds a profile to the list of profiles.
        Assumes this is called while the dialog is executing.
        """
        self.profiles.append(profile)
        new_index = len(self.profiles) - 1
        self.dlg.profiles_combobox.addItem(profile.name)
        self.dlg.profiles_combobox.setCurrentIndex(new_index)
        self.profile_changed_callback(new_index)

    def profile_changed_callback(self, i):
        self.save_profile_changes(self.current_profile_index)
        self.update_ui_for_profile(i)

    def update_ui_for_profile(self, i):
        profile = self.profiles[i]

        self.dlg.training_scenes_edit.setText(profile.training_scenes_sld)
        self.dlg.training_labels_edit.setText(profile.training_labels_sld)
        self.dlg.validation_scenes_edit.setText(profile.validation_scenes_sld)
        self.dlg.validation_labels_edit.setText(profile.validation_labels_sld)
        self.dlg.validation_predictions_edit.setText(profile.validation_predictions_sld)
        self.dlg.prediction_scenes_edit.setText(profile.prediction_scenes_sld)
        self.dlg.predictions_edit.setText(profile.predictions_sld)

        self.current_profile_index = i

    def save_profile_changes(self, i):
        profile = self.profiles[i]
        profile.training_scenes_sld = self.dlg.training_scenes_edit.text()
        profile.training_labels_sld = self.dlg.training_labels_edit.text()
        profile.validation_scenes_sld = self.dlg.validation_scenes_edit.text()
        profile.validation_labels_sld = self.dlg.validation_labels_edit.text()
        profile.validation_predictions_sld = self.dlg.validation_predictions_edit.text()
        profile.prediction_scenes_sld = self.dlg.prediction_scenes_edit.text()
        profile.predictions_sld = self.dlg.predictions_edit.text()

        self.profiles[i] = profile

    def run(self):
        settings = Settings()

        self.dlg.show()

        self.current_profile_index = settings.get_style_profiles_index()
        self.profiles = settings.get_style_profiles()

        # Block signals while loading the combobox
        old_state = self.dlg.profiles_combobox.blockSignals(True)
        self.dlg.profiles_combobox.clear()
        self.dlg.profiles_combobox.addItems(map(lambda p: p.name, self.profiles))
        self.dlg.profiles_combobox.setCurrentIndex(self.current_profile_index)
        self.update_ui_for_profile(self.current_profile_index)
        self.dlg.profiles_combobox.blockSignals(old_state)

        result = self.dlg.exec_()

        if result:
            self.save_profile_changes(self.current_profile_index)
            settings.set_style_profiles_index(self.dlg.profiles_combobox.currentIndex())
            settings.set_style_profiles(self.profiles)
