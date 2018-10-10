from .utils import get_local_path

from .log import Log

class RasterSourceLoader:
    @staticmethod
    def load(uri, layer_name, ctx, style_file=None):
        path = get_local_path(uri, ctx.working_dir)
        layer = ctx.iface.addRasterLayer(path, layer_name)
        if style_file:
            if style_file.endswith('.sld'):
                layer.loadSldStyle(style_file)
            else:
                layer.loadNamedStyle(style_file)



class GeoTiffSourceLoader:
    @staticmethod
    def load(config, layer_name, ctx, style_file=None):
        uris = config.uris
        if len(uris) == 1:
            RasterSourceLoader.load(uris[0], layer_name, ctx, style_file)
        else:
            for i, uri in enumerate(uris):
                name = "{}_{}".format(layer_name, i)
                RasterSourceLoader.load(uri, name, ctx, style_file)
        return uris


class ImageSourceLoader:
    @staticmethod
    def load(config, layer_name, ctx, style_file=None):
        uri = config.uris
        RasterSourceLoader.load(uri, layer_name, ctx, style_file)
