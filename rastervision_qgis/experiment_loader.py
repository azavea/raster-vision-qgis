import os
import json

from PyQt5.QtGui import QColor

from qgis.core import *

from .registry import RegistryInstance
from .log import Log
from .raster_util import get_raster_layers
from .label_loader import GeoJSONLoader

class LoadContext:
    def __init__(self, task, iface, style_profile, working_dir):
        self.task = task
        self.iface = iface
        self.style_profile = style_profile
        self.working_dir = working_dir

class SceneLoadOptions:
    def __init__(self,
                 scene_id,
                 load_image=True,
                 load_ground_truth=True,
                 load_predictions=True,
                 load_aoi=True):
        self.scene_id = scene_id
        self.load_image = load_image
        self.load_ground_truth = load_ground_truth
        self.load_predictions = load_predictions
        self.load_aoi = load_aoi

    def __repr__(self):
        load_i, load_gt, load_p = "", "", ""
        if self.load_image:
            load_i = " (IMAGE)"
        if self.load_ground_truth:
            load_gt = " (GROUND TRUTH)"
        if self.load_predictions:
            load_p = " (PREDICTIONS)"
        if self.load_aoi:
            load_p = " (AOI)"

        return "SCENE: {}{}{}{}".format(self.scene_id, load_i, load_gt, load_p)

class ExperimentLoadOptions:
    def __init__(self,
                 train_scenes=None,
                 validation_scenes=None,
                 test_scenes=None):
        if train_scenes is None:
            train_scenes = []
        if validation_scenes is None:
            validation_scenes = []
        if test_scenes is None:
            test_scenes = []
        self.train_scenes = dict(map(lambda s: (s.scene_id, s), train_scenes))
        self.validation_scenes = dict(map(lambda s: (s.scene_id, s), validation_scenes))
        self.test_scenes = dict(map(lambda s: (s.scene_id, s), test_scenes))
        Log.log_info("{}".format(train_scenes))
        Log.log_info("{}".format(validation_scenes))
        Log.log_info("{}".format(test_scenes))

class ExperimentLoader:
    @staticmethod
    def clear_layers():
        layer_ids = QgsProject.instance().mapLayers().keys()
        for layer_id in layer_ids:
            QgsProject.instance().removeMapLayer(layer_id)

    @staticmethod
    def zoom_to_layer(ctx):
        image_layers =  list(get_raster_layers().values())
        if image_layers:
            layer = image_layers[-1]
            ctx.iface.setActiveLayer(layer)
            ctx.iface.zoomToActiveLayer()
        else:
            project = QgsProject.instance()
            layers = list(project.mapLayers().values())
            if layers:
                layer = layers[-1]
                ctx.iface.setActiveLayer(layer)
                ctx.iface.zoomToActiveLayer()

    @staticmethod
    def load_scene(layer_prefix, scene, opts, ctx):
        layer_name = "{}{}".format(layer_prefix, scene.id)
        if opts.load_image:
            config = scene.raster_source
            loader = RegistryInstance.get().get_raster_source_loader(config.source_type)
            loader.load(config, layer_name, ctx)
        if opts.load_ground_truth and scene.label_source:
            config = scene.label_source
            loader = RegistryInstance.get().get_label_source_loader(config.source_type)
            gt_layer_name = "{}-ground_truth".format(layer_name)
            loader.load(config, gt_layer_name, ctx)
        if opts.load_predictions and scene.label_store:
            config = scene.label_store
            loader = RegistryInstance.get().get_label_store_loader(config.store_type)
            prediction_layer_name = "{}-predictions".format(layer_name)
            loader.load(config, prediction_layer_name, ctx)
        if opts.load_aoi and scene.aoi_uri:
            sld = None
            if ctx.style_profile:
                sld = ctx.style_profile.aoi_sld
            GeoJSONLoader.load(scene.aoi_uri, "{}-AOI".format(layer_name), ctx, sld)

    @staticmethod
    def load(experiment, options, ctx):
        ExperimentLoader.clear_layers()

        for scene in experiment.dataset.train_scenes:
            opts = options.train_scenes.get(scene.id)
            if opts:
                ExperimentLoader.load_scene("train-", scene, opts, ctx)

        for scene in experiment.dataset.validation_scenes:
            opts = options.validation_scenes.get(scene.id)
            if opts:
                ExperimentLoader.load_scene("val-", scene, opts, ctx)

        for scene in experiment.dataset.test_scenes:
            opts = options.test_scenes.get(scene.id)
            if opts:
                ExperimentLoader.load_scene("test-", scene, opts, ctx)

        # Dump any evaluatoions into the log if they exist
        for evaluator in experiment.evaluators:
            loader = RegistryInstance.get().get_evaluator_loader(evaluator.evaluator_type)
            if loader:
                loader.load(evaluator, ctx)

        ExperimentLoader.zoom_to_layer(ctx)
        return False
