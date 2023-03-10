from ..qgis_plugin_tools.tools.exceptions import QgsPluginException


class DatabaseNotSetException(QgsPluginException):
    pass

class AuthConfigException(QgsPluginException):
    pass

class InitializationCancelled(QgsPluginException):
    pass

class UnableToDropDatabase(QgsPluginException):
    pass

class UnableToConnectToDb(QgsPluginException):
    pass

class ProjectInInvalidFormat(QgsPluginException):
    pass