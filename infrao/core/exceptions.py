from ..qgis_plugin_tools.tools.exceptions import QgsPluginException


class DatabaseNotSetException(QgsPluginException):
    pass

class AuthConfigException(QgsPluginException):
    pass

class InitializationCancelled(QgsPluginException):
    pass