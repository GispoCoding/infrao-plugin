import logging
from typing import Dict

from PyQt5.QtCore import QSettings
from qgis.core import QgsDataSourceUri, QgsAuthMethodConfig, QgsApplication

from ..core.exceptions import AuthConfigException, DatabaseNotSetException
from ..qgis_plugin_tools.tools.custom_logging import bar_msg
from ..qgis_plugin_tools.tools.i18n import tr
from ..qgis_plugin_tools.tools.resources import plugin_name
from ..qgis_plugin_tools.tools.settings import parse_value, get_setting

LOGGER = logging.getLogger(plugin_name())
PG_CONNECTIONS = "PostgreSQL/connections"
QGS_SETTINGS_PSYCOPG2_PARAM_MAP = {
    'database': 'dbname',
    'host': 'host',
    'password': 'password',
    'port': 'port',
    'username': 'user'
}

def get_existing_database_connections() -> (str):
    """
    :return: set of connections names
    """
    s = QSettings()
    s.beginGroup(PG_CONNECTIONS)
    keys = s.allKeys()
    s.endGroup()
    connections = {key.split('/')[0] for key in keys if '/' in key}
    LOGGER.debug(f"Connections: {connections}")
    return connections

'''
def get_db_connection_uri() -> QgsDataSourceUri:
    """

    :param plan:
    :return:
    """
    conn_params = get_db_connection_params()
    uri = QgsDataSourceUri()
    uri.setConnection(conn_params['host'], conn_params['port'], conn_params['dbname'])
    return uri


def get_connection_name() -> str:
    """
    :return: Name of the PostGIS connection that will be used by the plugin
    """
    value = get_setting(value.key, "", str)
    if value == "":
        raise DatabaseNotSetException()
    return value

'''
def get_db_connection_params(con_name) -> Dict[str, str]:
    s = QSettings()
    s.beginGroup(f"{PG_CONNECTIONS}/{con_name}")
    auth_cfg_id = parse_value(s.value("authcfg"))
    username_saved = parse_value(s.value("saveUsername"))
    pwd_saved = parse_value(s.value("savePassword"))

    params = {}

    for qgs_key, psyc_key in QGS_SETTINGS_PSYCOPG2_PARAM_MAP.items():
        params[psyc_key] = parse_value(s.value(qgs_key))

    s.endGroup()
    # username or password might have to be asked separately
    if not username_saved:
        params["user"] = None

    if not pwd_saved:
        params["password"] = None

    if auth_cfg_id is not None and auth_cfg_id != "":
        LOGGER.debug(f"Auth cfg: {auth_cfg_id}")
        # Auth config is being used to store the username and password
        auth_config = QgsAuthMethodConfig()
        # noinspection PyArgumentList
        QgsApplication.authManager().loadAuthenticationConfig(auth_cfg_id, auth_config, True)

        if auth_config.isValid():
            params["user"] = auth_config.configMap().get("username")
            params["password"] = auth_config.configMap().get("password")
        else:
            raise AuthConfigException(
                tr("Auth config error occurred while fetching database connection parameters"),
                bar_msg=bar_msg(tr(f"Check auth config with id: {auth_cfg_id}")))

    return params