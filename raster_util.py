from qgis.core import (QgsProject,
                       QgsRasterFileWriter,
                       QgsRasterLayer,
                       QgsRasterPipe)

def export_raster_layer(layer, path):
    provider = layer.dataProvider()
    renderer = layer.renderer()
    pipe = QgsRasterPipe()
    pipe.set(provider.clone())
    pipe.set(renderer.clone())

    file_writer = QgsRasterFileWriter(path)
    file_writer.writeRaster(
        pipe,
        provider.xSize(),
        provider.ySize(),
        provider.extent(),
        raster.crs())

def get_raster_layers():
    project = QgsProject.instance()
    raster_layers = { }
    for layer in project.mapLayers().values():
        if type(layer) is QgsRasterLayer:
            raster_layers[layer.name()] = layer
    return raster_layers
