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

from .file_util import get_local_path

class VizWorkflow(object):
    def __init__(self,
                 iface,
                 rv_root,
                 workflow_path,
                 working_dir,
                 aws_profile,
                 style_profile):
        self.iface = iface
        self.rv_root = rv_root
        self.workflow_path = workflow_path
        self.working_dir = working_dir
        self.aws_profile = aws_profile
        self.style_profile = style_profile

    def get_local_path(self, uri):
        return get_local_path(uri, self.working_dir, self.aws_profile)

    def show(self):
        self.viz_workflow()

    def load_json(self, uri):
        path = self.get_local_path(uri)
        if path:
            with open(path, 'r') as f:
                return json.load(f)
        else:
            raise Exception("Could not load {}".format(uri))

    def make_vector_renderer(self, layer, class_field, class_items, is_pred=False):
        category_map = {}

        # TODO: Color Assignment
        colors = ['Blue', 'Red', 'Green', 'Yellow']

        for i, class_item in enumerate(class_items):
            name = class_item['name']
            color = class_item.get('color', colors[i % len(colors)])
            category_map[name] = (color, name)

        categories = []
        for name, (color, label) in category_map.items():
            symbol = QgsSymbol.defaultSymbol(layer.geometryType())
            if not is_pred:
                symbol_layer = QgsSimpleLineSymbolLayer()
                symbol_layer.setWidth(0.5)
                symbol.changeSymbolLayer(0, symbol_layer)
                symbol.setColor(QColor(color))
            else:
                # props = {'color':'red', 'style': 'f_diagonal' }
                # symbol_layer = QgsLinePatternFillSymbolLayer.create(props)
                # symbol.changeSymbolLayer(0, symbol_layer)
                # symbol.setColor(QColor(color))

                symbol_layer = QgsSimpleLineSymbolLayer()
                symbol_layer.setWidth(1.0)
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
        eval = self.load_json(eval_uri)
        print(json.dumps(eval, indent=2))

    def add_raster_layer(self, layer_name, path, sld=None):
        raster_layer = self.iface.addRasterLayer(path, layer_name)

        if sld:
            layer.loadSldStyle(sld)

    def viz_scenes(self, workflow):
        channel_order = workflow['raster_transformer']['channel_order']
        for scene in workflow['test_scenes']:
            id = scene['id']
            is_classification = workflow['machine_learning']['task'] == 'CLASSIFICATION'
            key = 'classification_geojson_file' \
                if is_classification else 'object_detection_geojson_file'
            class_items = workflow['machine_learning']['class_items']

            raster_uris = scene['raster_source']['geotiff_files']['uris']
            raster_uris = [uri.format(rv_root=self.rv_root) for uri in raster_uris]
            for raster_uri in raster_uris:
                raster_path = self.get_local_path(raster_uri)
                fname = os.path.splitext(os.path.basename(raster_path))[0]
                layer_name = "validation-scene-{}_{}".format(fname, id)
                sld = None
                if self.style_profile and self.style_profile.validation_scenes_sld:
                    sld = style_profile.validation_scenes_sld

                self.add_raster_layer(layer_name, raster_path, sld)

            gt_labels_uri = (
                scene['ground_truth_label_store'][key]
                ['uri'].format(rv_root=self.rv_root))
            gt_labels_path = self.get_local_path(gt_labels_uri)
            if gt_labels_path:
                gt_layer = self.iface.addVectorLayer(
                    gt_labels_path, 'validation-ground-truth-' + id, 'ogr')
                if self.style_profile and self.style_profile.validation_labels_sld:
                    gt_layer.loadSldStyle(self.style_profile.validation_labels_sld)
                else:
                    class_field = self.get_class_field(gt_labels_uri)
                    renderer = self.make_vector_renderer(gt_layer, class_field, class_items)
                    gt_layer.setRenderer(renderer)

            prediction_labels_uri = os.path.join(
                self.rv_root, 'rv-output', 'raw-datasets', workflow['raw_dataset_key'],
                'datasets', workflow['dataset_key'], 'models', workflow['model_key'],
                'predictions', workflow['prediction_key'], 'output', id + '.json')
            prediction_labels_path = self.get_local_path(prediction_labels_uri)
            if prediction_labels_path:
                pred_layer = self.iface.addVectorLayer(
                    prediction_labels_path, 'validation-predictions-' + id, 'ogr')
                if self.style_profile and self.style_profile.validation_predictions_sld:
                    pred_layer.loadSldStyle(self.style_profile.validation_predictions_sld)
                else:
                    class_field = self.get_class_field(prediction_labels_path)
                    renderer = self.make_vector_renderer(pred_layer, class_field, class_items, is_pred=True)
                    pred_layer.setRenderer(renderer)

    def viz_workflow(self):
        self.clear_layers()

        workflow = self.load_json(self.workflow_path)

        eval_uri = os.path.join(
            self.rv_root, 'rv-output', 'raw-datasets', workflow['raw_dataset_key'],
            'datasets', workflow['dataset_key'], 'models', workflow['model_key'],
            'predictions', workflow['prediction_key'], 'evals',
            workflow['eval_key'], 'output', 'eval.json')

        self.dump_eval(eval_uri)

        self.viz_scenes(workflow)
