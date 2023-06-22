#  Gispo Ltd., hereby disclaims all copyright interest in the program infrao-plugin
#  Copyright (C) 2023 Gispo Ltd (https://www.gispo.fi/).
#
#
#  This file is part of infrao-plugin.
#
#  infrao-plugin is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 2 of the License, or
#  (at your option) any later version.
#
#  infrao-plugin is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with infrao-plugin.  If not, see <https://www.gnu.org/licenses/>.

import logging
import zipfile
import binascii
import io
import re
from zipfile import ZipFile
from typing import Dict, Union, List, Optional

from qgis.utils import iface
from ..ui.ask_credentials import DbAskCredentialsDialog



from PyQt5.QtCore import QSettings
from qgis.core import QgsAuthManager, QgsAuthMethodConfig, QgsApplication

from ..core.exceptions import AuthConfigException, DatabaseNotSetException, ProjectInInvalidFormat
from ..qgis_plugin_tools.tools.custom_logging import bar_msg
from ..qgis_plugin_tools.tools.i18n import tr
from ..qgis_plugin_tools.tools.resources import plugin_name
from ..qgis_plugin_tools.tools.settings import parse_value, set_setting

LOGGER = logging.getLogger(plugin_name())
PG_CONNECTIONS = "PostgreSQL/connections"
QGS_SETTINGS_PSYCOPG2_PARAM_MAP = {
    'database': 'dbname',
    'host': 'host',
    'password': 'password',
    'port': 'port',
    'username': 'user',
    'sslmode': 'sslmode',
}

QGS_SETTINGS_SSL_MODE_TO_POSTGRES = {
    'SslDisable': 'disable',
    'SslAllow': 'allow',
    'SslPrefer': 'prefer',
    'SslRequire': 'require',
    'SslVerifyCa': 'verify-ca',
    'SslVerifyFull': 'verify-full',
}

def fix_data_sources_from_binary_projects(conn_params, auth_cfg_id, contents): #conn_params, auth_cfg_id, contents
    host = conn_params['host']
    port = conn_params['port']
    dbname = conn_params['dbname']
    sslmode = conn_params['sslmode']

    ret_vals = []
    conn_string = f"dbname='{dbname}' host={host} port={port} sslmode={sslmode} authcfg={auth_cfg_id} key="
    for i, content in enumerate(contents):
        z = io.BytesIO()
        z.write(content)
        files = extract_zip(z)
        #assert len(files) == 2
        qgs_f_key = [f for f in files.keys() if f.endswith('.qgs')][0]
        qgs_proj_content = files[qgs_f_key].decode('utf-8')
        # Replace all connection string from layers with the db specific connection string
        qgs_proj_content = re.sub(r'dbname=.*host=.*port=\d{4}.*sslmode=.*authcfg=.*key=', conn_string, qgs_proj_content)
        if conn_string not in qgs_proj_content:
            raise ProjectInInvalidFormat()
        files[qgs_f_key] = bytes(qgs_proj_content, 'utf-8')
        ret_vals.append(create_in_memory_zip(files))
    return ret_vals
    
    



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

def extract_zip(input_zip):
    input_zip = ZipFile(input_zip)
    return {name: input_zip.read(name) for name in input_zip.namelist()}


def create_in_memory_zip(contents: Dict[str, bytes]) -> bytes:
    zip_buffer = io.BytesIO()
    with ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
        for file_name, data in contents.items():
            zip_file.writestr(file_name, io.BytesIO(data).getvalue())
    return binascii.hexlify(zip_buffer.getvalue())


def get_db_connection_params(con_name) -> Dict[str, str]:
    s = QSettings()
    s.beginGroup(f"{PG_CONNECTIONS}/{con_name}")
    
    auth_cfg_id = parse_value(s.value("authcfg"))
    username_saved = parse_value(s.value("saveUsername"))
    pwd_saved = parse_value(s.value("savePassword"))
    sslmode = parse_value(s.value("sslmode"))

    params = {}

    for qgs_key, psyc_key in QGS_SETTINGS_PSYCOPG2_PARAM_MAP.items():
        if psyc_key != 'sslmode':
            params[psyc_key] = parse_value(s.value(qgs_key))
        else:
            params[psyc_key] = QGS_SETTINGS_SSL_MODE_TO_POSTGRES[parse_value(s.value(qgs_key))]

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


def check_credentials(conn_params):
    if not conn_params['password'] or not conn_params['user']:
        LOGGER.info("No username and/or password found.")
        ask_credentials_dlg = DbAskCredentialsDialog()
        result = ask_credentials_dlg.exec_()
        if (result):
            conn_params['user'] = ask_credentials_dlg.userLineEdit.text()
            conn_params['password'] = ask_credentials_dlg.pwdLineEdit.text()
        else:
            ask_credentials_dlg.close()
            iface.messageBar().pushMessage("Ei voi alustaa ilman käyttäjänimeä tai salasanaa.", level=1, duration=5)
            return 


def set_auth_cfg(auth_cfg_key: str, auth_cfg_id: str, username: str, password: str) -> None:
    """
    :param auth_cfg_id:
    :param username:
    :param password:
    """
    # noinspection PyArgumentList
    auth_mgr: QgsAuthManager = QgsApplication.authManager()
    if auth_cfg_id in auth_mgr.availableAuthMethodConfigs().keys():
        config = QgsAuthMethodConfig()
        auth_mgr.loadAuthenticationConfig(auth_cfg_id, config, True)
        config.setConfig('username', username)
        config.setConfig('password', password)
        if not config.isValid():
            raise AuthConfigException('Invalid username or password')
        auth_mgr.updateAuthenticationConfig(config)
    else:
        config = QgsAuthMethodConfig()
        config.setId(auth_cfg_id)
        config.setName(auth_cfg_id)
        config.setMethod('Basic')
        config.setConfig('username', username)
        config.setConfig('password', password)
        if not config.isValid():
            raise AuthConfigException('Invalid username or password')
        auth_mgr.storeAuthenticationConfig(config)

    set_setting(auth_cfg_key, auth_cfg_id, internal=False)