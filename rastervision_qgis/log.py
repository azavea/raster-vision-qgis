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
