from .utils import get_local_path

from .log import Log

class GeoTiffSourceLoader:
    @staticmethod
    def load(config, layer_name, ctx):
        sld = None
        if ctx.style_profile and ctx.style_profile.image_sld:
            sld = ctx.style_profile.image_sld

        def _load(name, uri):
            path = get_local_path(uri, ctx.working_dir)
            layer = ctx.iface.addRasterLayer(path, name)
            if sld:
                layer.loadSldStyle(sld)

        uris = config.uris
        if len(uris) == 1:
            _load(layer_name, uris[0])
        else:
            for i, uri in enumerate(uris):
                name = "{}_{}".format(layer_name, i)
                _load(name, uri)
        return uris


class ImageSourceLoader:
    @staticmethod
    def load(config, layer_name, ctx):
        raise  NotImplementedError()
