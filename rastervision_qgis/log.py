import traceback

from qgis.core import Qgis, QgsMessageLog

class Log:
    @classmethod
    def log_info(cls, msg):
        QgsMessageLog.logMessage(msg, tag="Raster Vision", level=Qgis.Info)

    @classmethod
    def log_warning(cls, msg):
        QgsMessageLog.logMessage(msg, tag="Raster Vision", level=Qgis.Warning)

    @classmethod
    def log_error(cls, msg):
        QgsMessageLog.logMessage(msg, tag="Raster Vision", level=Qgis.Critical)

    @classmethod
    def log_exception(cls, e):
        e_traceback = e.__traceback__
        tb_lines = [ line.rstrip('\n') for line in
                     traceback.format_exception(e.__class__, e, e_traceback)]
        cls.log_error(''.join(tb_lines))
