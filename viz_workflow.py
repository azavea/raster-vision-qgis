"""QGIS 3.0 script to visualize predictions and eval from a workflow config.

Given a workflow config and the output of running the workflow, this
script will add styled raster and vector layers to compare the predictions to
the ground truth for each of the test scenes. It also prints the eval to the
console. To run this script, it should be copied into the QGIS Python console,
and the rv_root and workflow_path variables at the bottom should be set.
"""
import os
import json

from PyQt5.QtGui import QColor

from qgis.core import *

from .experiment_files import ExperimentFiles
from .file_util import get_local_path
from .log import Log

class ExperimentLoadOptions:
    def __init__(self, training_scenes=True, training_labels=True,
                 validation_scenes=True, validation_labels=True, validation_predictions=True,
                 prediction_scenes=True, predictions=True):
        self.training_scenes = training_scenes
        self.training_labels = training_labels
        self.validation_scenes = validation_scenes
        self.validation_labels = validation_labels
        self.validation_predictions = validation_predictions
        self.prediction_scenes = prediction_scenes
        self.predictions = predictions

    def to_json(self):
        return { 'training_scenes': self.training_scenes,
                 'training_labels': self.training_labels,
                 'validation_scenes': self.validation_scenes,
                 'validation_labels': self.validation_labels,
                 'validation_predictions': self.validation_predictions,
                 'prediction_scenes': self.prediction_scenes,
                 'predictions': self.predictions }

    @classmethod
    def from_json(cls, json):
        return ExperimentLoadOptions(json['training_scenes'],
                                     json['training_labels'],
                                     json['validation_scenes'],
                                     json['validation_labels'],
                                     json['validation_predictions'],
                                     json['prediction_scenes'],
                                     json['predictions'])

class VizWorkflow(object):
    def __init__(self,
                 iface,
                 rv_root,
                 workflow_uri,
                 working_dir,
                 aws_profile,
                 style_profile,
                 options):
        self.iface = iface
        self.rv_root = rv_root
        self.workflow_uri = workflow_uri
        self.working_dir = working_dir
        self.aws_profile = aws_profile
        self.style_profile = style_profile
        self.options = options

    def get_local_path(self, uri):
        return get_local_path(uri, self.working_dir, self.aws_profile)

    def show(self):
        return self.viz_workflow()

    def load_json(self, uri):
        path = self.get_local_path(uri)
        if path:
            with open(path, 'r') as f:
                return json.load(f)
        else:
            None

    def make_vector_renderer(self, layer, class_field, class_items):
        category_map = {}

        # TODO: Better Color Assignment?
        colors = ['Blue', 'Red', 'Green', 'Yellow']

        for i, class_item in enumerate(class_items):
            name = class_item['name']
            color = class_item.get('color', colors[i % len(colors)])
            category_map[name] = (color, name)

        categories = []
        for name, (color, label) in category_map.items():
            symbol = QgsSymbol.defaultSymbol(layer.geometryType())
            symbol_layer = QgsSimpleLineSymbolLayer()
            symbol_layer.setWidth(0.5)
            symbol.changeSymbolLayer(0, symbol_layer)
            symbol.setColor(QColor(color))

            category = QgsRendererCategory(label, symbol, name)
            categories.append(category)

        renderer = QgsCategorizedSymbolRenderer(class_field, categories)
        return renderer


    def get_class_field(self, labels_uri):
        labels = self.load_json(labels_uri)
        feature = labels['features'][0]
        properties = feature.get('properties', {})
        if 'class_name' in properties:
            return 'class_name'
        return 'label'


    def clear_layers(self):
        layer_ids = QgsProject.instance().mapLayers().keys()
        for layer_id in layer_ids:
            QgsProject.instance().removeMapLayer(layer_id)

    def dump_eval(self, eval_uri):
        eval_data = self.load_json(eval_uri)
        if eval_data:
            Log.log_info(json.dumps(eval_data, indent=2))

    def add_raster_layer(self, layer_name, path, sld=None):
        raster_layer = self.iface.addRasterLayer(path, layer_name)

        if sld:
            layer.loadSldStyle(sld)

    def viz_scenes(self, workflow, experiment_files):
        class_items = experiment_files.class_items
        errors = False

        # Training Data
        for id, scene_data in experiment_files.training_set.items():
            if self.options.training_scenes:
                if scene_data.raster_uris:
                    for raster_uri in scene_data.raster_uris:
                        raster_path = self.get_local_path(raster_uri)
                        if raster_path:
                            fname = os.path.splitext(os.path.basename(raster_path))[0]
                            layer_name = "training-scene-{}_{}".format(fname, id)
                            sld = None
                            if self.style_profile and self.style_profile.validation_scenes_sld:
                                sld = style_profile.validation_scenes_sld

                            self.add_raster_layer(layer_name, raster_path, sld)
                        else:
                            errors = True
                            Log.log_warning("Cannot load raster at {}".format(raster_uri))
                else:
                    errors = True
                    Log.log_warning("Training Scenes do not exist in this workflow.")

            if self.options.training_labels:
                gt_labels_uri = scene_data.ground_truth_label_uri
                if gt_labels_uri:
                    gt_labels_path = self.get_local_path(gt_labels_uri)
                    if gt_labels_path:
                        gt_layer = self.iface.addVectorLayer(
                            gt_labels_path, 'training-ground-truth-' + id, 'ogr')
                        if self.style_profile and self.style_profile.validation_labels_sld:
                            gt_layer.loadSldStyle(self.style_profile.validation_labels_sld)
                        else:
                            class_field = self.get_class_field(gt_labels_uri)
                            renderer = self.make_vector_renderer(gt_layer, class_field, class_items)
                            gt_layer.setRenderer(renderer)
                    else:
                        errors = True
                        Log.log_warning("Cannot load GeoJSON at {}".format(gt_labels_uri))
                else:
                    errors = True
                    Log.log_warning("Training Labels do not exist in this workflow.")

        # Valdation Data
        for id, scene_data in experiment_files.validation_set.items():
            if self.options.validation_scenes:
                if scene_data.raster_uris:
                    for raster_uri in scene_data.raster_uris:
                        raster_path = self.get_local_path(raster_uri)
                        if raster_path:
                            fname = os.path.splitext(os.path.basename(raster_path))[0]
                            layer_name = "validation-scene-{}_{}".format(fname, id)
                            sld = None
                            if self.style_profile and self.style_profile.validation_scenes_sld:
                                sld = style_profile.validation_scenes_sld

                            self.add_raster_layer(layer_name, raster_path, sld)
                        else:
                            Log.log_warning("Cannot load raster at {}".format(raster_uri))
                else:
                    errors = True
                    Log.log_warning("Validation Scenes do not exist in this workflow.")


            if self.options.validation_labels:
                gt_labels_uri = scene_data.ground_truth_label_uri
                if gt_labels_uri:
                    gt_labels_path = self.get_local_path(gt_labels_uri)
                    if gt_labels_path:
                        gt_layer = self.iface.addVectorLayer(
                            gt_labels_path, 'valiation-ground-truth-' + id, 'ogr')
                        if self.style_profile and self.style_profile.validation_labels_sld:
                            gt_layer.loadSldStyle(self.style_profile.validation_labels_sld)
                        else:
                            class_field = self.get_class_field(gt_labels_uri)
                            renderer = self.make_vector_renderer(gt_layer, class_field, class_items)
                            gt_layer.setRenderer(renderer)
                    else:
                        errors = True
                        Log.log_warning("Cannot load GeoJSON at {}".format(gt_labels_uri))
                else:
                    errors = True
                    Log.log_warning("Validation Labels do not exist in this workflow.")

            if self.options.validation_predictions:
                pr_labels_uri = scene_data.prediction_uri
                if pr_labels_uri:
                    pr_labels_path = self.get_local_path(pr_labels_uri)
                    if pr_labels_path:
                        pr_layer = self.iface.addVectorLayer(
                            pr_labels_path, 'validation-predictions-' + id, 'ogr')
                        if self.style_profile and self.style_profile.validation_predictions_sld:
                            pr_layer.loadSldStyle(self.style_profile.validation_predictions_sld)
                        else:
                            class_field = self.get_class_field(pr_labels_uri)
                            renderer = self.make_vector_renderer(gt_layer, class_field, class_items)
                            pr_layer.setRenderer(renderer)
                    else:
                        errors = True
                        Log.log_warning("Cannot load GeoJSON at {}".format(pr_labels_uri))
                else:
                    errors = True
                    Log.log_warning("Validation Predictions do not exist in this workflow.")


        # Prediction Data
        for id, scene_data in experiment_files.prediction_set.items():
            if self.options.prediction_scenes:
                if scene_data.raster_uris:
                    for raster_uri in scene_data.raster_uris:
                        raster_path = self.get_local_path(raster_uri)
                        if raster_path:
                            fname = os.path.splitext(os.path.basename(raster_path))[0]
                            layer_name = "prediction-scene-{}_{}".format(fname, id)
                            sld = None
                            if self.style_profile and self.style_profile.prediction_scenes_sld:
                                sld = style_profile.prediction_scenes_sld

                            self.add_raster_layer(layer_name, raster_path, sld)
                        else:
                            Log.log_warning("Cannot load raster at {}".format(raster_uri))
                else:
                    errors = True
                    Log.log_warning("Prediction Scenes do not exist in this workflow.")

            if self.options.predictions:
                pr_labels_uri = scene_data.prediction_uri
                if pr_labels_uri:
                    pr_labels_path = self.get_local_path(pr_labels_uri)
                    if pr_labels_path:
                        pr_layer = self.iface.addVectorLayer(
                            pr_labels_path, 'predictions-' + id, 'ogr')
                        if self.style_profile and self.style_profile.prediction_predictions_sld:
                            pr_layer.loadSldStyle(self.style_profile.prediction_predictions_sld)
                        else:
                            class_field = self.get_class_field(pr_labels_uri)
                            renderer = self.make_vector_renderer(gt_layer, class_field, class_items)
                            pr_layer.setRenderer(renderer)
                    else:
                        errors = True
                        Log.log_warning("Cannot load GeoJSON at {}".format(pr_labels_uri))
                else:
                    errors = True
                    Log.log_warning("Predictions do not exist in this workflow.")

        self.iface.zoomToActiveLayer()

        return errors

    def viz_workflow(self):
        self.clear_layers()

        workflow = self.load_json(self.workflow_uri)
        if not workflow:
            Log.log_error("Cannot load workflow at {}".format(self.workflow_uri))
            return True

        Log.log_info("Loading experiment form workflow at {}".format(self.workflow_uri))

        experiment_files = ExperimentFiles.from_workflow_config(workflow, self.rv_root)

        eval_uri = os.path.join(
            self.rv_root, 'rv-output', 'raw-datasets', workflow['raw_dataset_key'],
            'datasets', workflow['dataset_key'], 'models', workflow['model_key'],
            'predictions', workflow['prediction_key'], 'evals',
            workflow['eval_key'], 'output', 'eval.json')

        self.dump_eval(eval_uri)

        return self.viz_scenes(workflow, experiment_files)
