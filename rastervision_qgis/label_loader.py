import json

from PyQt5.QtGui import QColor
from qgis.core import (QgsSymbol,
                       QgsSimpleLineSymbolLayer,
                       QgsRendererCategory,
                       QgsCategorizedSymbolRenderer)

from .utils import get_local_path


class GeoJSONLoader:
    @staticmethod
    def _get_class_field(labels_uri):
        potentials = ['className', 'class_name', 'label']
        labels = None
        with open(labels_uri) as f:
            labels = json.loads(f.read())
        feature = labels['features'][0]
        properties = feature.get('properties', {})
        for field in potentials:
            if field in properties:
                return field
        return potentials[0]

    @staticmethod
    def _make_vector_renderer(layer, class_field, class_map):
        category_map = {}

        colors = ['Blue', 'Red', 'Green', 'Yellow']

        for i, class_item in enumerate(class_map.get_items()):
            name = class_item.name
            color = class_item.color
            if color is None:
                color = colors[i % len(colors)]
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


    @staticmethod
    def load(uri, layer_name, ctx, sld=None):
        path = get_local_path(uri, ctx.working_dir)
        layer = ctx.iface.addVectorLayer(path, layer_name, 'ogr')
        if sld:
            layer.loadSldStyle(sld)
        else:
            class_map = ctx.task.class_map
            class_field = GeoJSONLoader._get_class_field(path)
            renderer = GeoJSONLoader._make_vector_renderer(layer, class_field, class_map)
            layer.setRenderer(renderer)
        return uri


class GeoJSONGroundTruthLoader:
    @staticmethod
    def load(config, layer_name, ctx):
        sld = None
        if ctx.style_profile:
            sld = ctx.style_profile.ground_truth_sld
        return GeoJSONLoader.load(config.uri, layer_name, ctx, sld)

class GeoJSONPredictionLoader:
    @staticmethod
    def load(config, layer_name, ctx):
        sld = None
        if ctx.style_profile:
            sld = ctx.style_profile.prediction_sld
        return GeoJSONLoader.load(config.uri, layer_name, ctx, sld)
