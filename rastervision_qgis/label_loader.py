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
    def load(uri, layer_name, ctx, style_file=None):
        path = get_local_path(uri, ctx.working_dir)
        layer = ctx.iface.addVectorLayer(path, layer_name, 'ogr')
        if style_file:
            if style_file.endswith('.sld'):
                layer.loadSldStyle(style_file)
            else:
                layer.loadNamedStyle(style_file)
        else:
            class_map = ctx.task.class_map
            class_field = GeoJSONLoader._get_class_field(path)
            renderer = GeoJSONLoader._make_vector_renderer(layer, class_field, class_map)
            layer.setRenderer(renderer)


class GeoJSONUriLoader:
    @staticmethod
    def load(config, layer_name, ctx, style_file=None):
        GeoJSONLoader.load(config.uri, layer_name, ctx, style_file)


class RasterGroundTruthLoader:
    @staticmethod
    def load(config, layer_name, ctx, style_file=None):
        loader = ctx.registry.get_raster_source_loader(config.source.source_type)
        return loader.load(config.source, layer_name, ctx, style_file)


class RasterPredictionLoader:
    @staticmethod
    def load(config, layer_name, ctx, style_file=None):
        uri = config.uri
        path = get_local_path(uri, ctx.working_dir)
        layer = ctx.iface.addRasterLayer(path, layer_name)
        if style_file:
            if style_file.endswith('.sld'):
                layer.loadSldStyle(style_file)
            else:
                layer.loadNamedStyle(style_file)

        return layer
