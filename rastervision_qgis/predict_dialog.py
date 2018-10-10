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
from tempfile import TemporaryDirectory
# from subprocess import (Popen, PIPE, CalledProcessError)
from subprocess import (check_output, CalledProcessError)

from PyQt5 import uic
from PyQt5 import QtWidgets

import rastervision as rv
from rastervision.predictor import Predictor
from rastervision.utils.files import (download_if_needed, load_json_config)
from rastervision.protos.command_pb2 \
    import CommandConfig as CommandConfigMsg

from .registry import RegistryInstance
from .experiment_loader import  LoadContext
from .raster_util import (get_raster_layers, export_raster_layer)
from .settings import Settings, StyleProfile
from .log import Log


FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'predict_dialog_base.ui'))


class PredictDialog(QtWidgets.QDialog, FORM_CLASS):
    def __init__(self, parent=None):
        """Constructor."""

        super(PredictDialog, self).__init__(parent)
        self.setupUi(self)


class PredictDialogController(object):
    def __init__(self, iface):
        self.dlg = PredictDialog()
        self.iface = iface

    def run(self):
        self.dlg.show()

        settings = Settings()

        self.dlg.predict_package_edit.setText(settings.get_predict_package())

        self.dlg.style_profile_combobox.clear()
        profiles = settings.get_style_profiles()
        profiles.insert(0, StyleProfile.EMPTY())
        profile_names = list(map(lambda p: p.name, profiles))
        self.dlg.style_profile_combobox.addItems(profile_names)
        settings_profile = settings.get_predict_profile()
        if settings_profile in profile_names:
            self.dlg.style_profile_combobox.setCurrentIndex(profile_names.index(settings_profile))
        else:
            self.dlg.style_profile_combobox.setCurrentIndex(0)

        self.dlg.label_uri_edit.setText(settings.get_label_store_uri())

        self.dlg.update_stats_checkbox.setChecked(settings.get_update_stats())

        self.dlg.use_docker_checkbox.setChecked(settings.get_use_docker())
        self.dlg.docker_image_edit.setText(settings.get_docker_image())

        # Load all raster layers
        self.dlg.input_layer_combobox.clear()
        raster_layers = get_raster_layers()
        layer_names = []
        for name in raster_layers:
            layer_names.append(name)
            self.dlg.input_layer_combobox.addItem(name)

        result = self.dlg.exec_()

        if result:
            predict_package = self.dlg.predict_package_edit.text()
            settings.set_predict_package(predict_package)

            layer_name_idx = self.dlg.input_layer_combobox.currentIndex()
            layer_name = layer_names[layer_name_idx]
            layer = raster_layers[layer_name]

            style_profile_index = self.dlg.style_profile_combobox.currentIndex()
            settings.set_predict_profile(profile_names[style_profile_index])

            style_profile = None
            if not style_profile_index == 0:
                style_profile = profiles[style_profile_index]

            label_store_uri = self.dlg.label_uri_edit.text()
            settings.set_label_store_uri(label_store_uri)

            update_stats = self.dlg.update_stats_checkbox.checkState()
            settings.set_update_stats(update_stats)

            use_docker = self.dlg.use_docker_checkbox.checkState()
            settings.set_use_docker(use_docker)
            docker_image = self.dlg.docker_image_edit.text()
            settings.set_docker_image(docker_image)

            prediction_layer_name = '{}-predictions'.format(layer_name)

            with TemporaryDirectory(dir=settings.get_working_dir()) as tmp_dir:
                path = os.path.join(tmp_dir, "{}.tif".format(layer_name))
                export_raster_layer(layer, path)
                if not os.path.exists(path):
                    raise Exception("Writing raster to {} failed".format(path))
                bundle_config_base = 'bundle_config.json'
                bundle_config_path = os.path.join(tmp_dir, bundle_config_base)

                # Grab the predict package locally
                pp_local = download_if_needed(predict_package, tmp_dir)

                if use_docker:
                    pp_dir = os.path.dirname(pp_local)
                    pp_base = os.path.basename(pp_local)
                    gt_base = os.path.basename(path)
                    lb_dir = os.path.dirname(label_store_uri)
                    lb_base = os.path.basename(label_store_uri)

                    cmd = ['docker', 'run', '--rm',
                           '-v', '{}/.rastervision:/root/.rastervision'.format(os.environ['HOME']),
                           '-v', '{}:{}'.format(tmp_dir, '/opt/source'),
                           '-v', '{}:{}'.format(lb_dir, '/opt/output'),
                           '-v', '{}:{}'.format(pp_dir, '/opt/predict_package'),
                           docker_image, 'rastervision', 'predict',
                           '/opt/predict_package/{}'.format(pp_base),
                           '/opt/source/{}'.format(gt_base),
                           '/opt/output/{}'.format(lb_base),
                           '--export-config',
                           '/opt/source/{}'.format(bundle_config_base)]

                    if update_stats:
                        cmd.append('--update-stats')

                    Log.log_info('Running command: {}'.format(' '.join(cmd)))
                    try:
                        output = check_output(cmd)
                        Log.log_info("[PREDICT OUTPUT]: {}".format(output))
                    except CalledProcessError as e:
                        Log.log_error("Error running {}: {}".format(
                            ' '.join(cmd), e.output))
                        raise e
                else:
                    predictor = Predictor(pp_local, tmp_dir, update_stats=update_stats)
                    predictor.predict(path, label_store_uri, bundle_config_path)

                msg = load_json_config(bundle_config_path, CommandConfigMsg())
                bundle_config = msg.bundle_config
                task_config = rv.TaskConfig.from_proto(bundle_config.task)

                scene_config = rv.SceneConfig.from_proto(bundle_config.scene)
                label_store_config = scene_config.label_store.for_prediction(label_store_uri)

            # Load prediction
            config = label_store_config
            loader = RegistryInstance.get().get_label_store_loader(config.store_type)
            ctx = LoadContext(task_config, self.iface, style_profile, None)
            style_file = None
            if ctx.style_profile:
                style_file = ctx.style_profile.prediction_style_file
            loader.load(config, prediction_layer_name, ctx, style_file)
