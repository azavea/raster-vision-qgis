import rastervision as rv
from .raster_source_loader import (GeoTiffSourceLoader, ImageSourceLoader)
from .label_loader import (GeoJSONUriLoader, RasterGroundTruthLoader, RasterPredictionLoader)
from .evaluator_loader import JsonEvaluatorLoader

class RegistryError(Exception):
    pass


class Registry:
    """Singleton that holds instances of Raster Vision QGIS types,
       to be referenced by configuration code by key.
    """

    def __init__(self):
        self.raster_source_loaders = {
            # Raster Sources
            rv.GEOTIFF_SOURCE: GeoTiffSourceLoader,
            rv.IMAGE_SOURCE: ImageSourceLoader,
            rv.GEOJSON_SOURCE: GeoJSONUriLoader
        }

        self.label_source_loaders = {
            # Label Sources
            rv.OBJECT_DETECTION_GEOJSON: GeoJSONUriLoader,
            rv.CHIP_CLASSIFICATION_GEOJSON: GeoJSONUriLoader,
            rv.SEMANTIC_SEGMENTATION_RASTER: RasterGroundTruthLoader
        }

        self.label_store_loaders = {
            # Label Stores
            rv.OBJECT_DETECTION_GEOJSON: GeoJSONUriLoader,
            rv.CHIP_CLASSIFICATION_GEOJSON: GeoJSONUriLoader,
            rv.SEMANTIC_SEGMENTATION_RASTER: RasterPredictionLoader
        }

        self.evaluator_loaders = {
            # Evaluators
            rv.CHIP_CLASSIFICATION_EVALUATOR: JsonEvaluatorLoader,
            rv.OBJECT_DETECTION_EVALUATOR: JsonEvaluatorLoader
        }

    def get_raster_source_loader(self, key):
        loader = self.raster_source_loaders.get(key)

        if loader:
            return loader
        else:
            raise RegistryError('Unknown raster source loader {}'.format(key))

    def get_label_source_loader(self, key):
        loader = self.label_source_loaders.get(key)

        if loader:
            return loader
        else:
            raise RegistryError('Unknown label source loader {}'.format(key))

    def get_label_store_loader(self, key):
        loader = self.label_store_loaders.get(key)

        if loader:
            return loader
        else:
            raise RegistryError('Unknown label store loader {}'.format(key))

    def get_evaluator_loader(self, key):
        loader = self.evaluator_loaders.get(key)

        if loader:
            return loader
        else:
            # Don't error if we can't render this evaluator.
            return None

class RegistryInstance:
    registry = None

    @staticmethod
    def get():
        if RegistryInstance.registry is None:
            RegistryInstance.registry = Registry()
        return RegistryInstance.registry
