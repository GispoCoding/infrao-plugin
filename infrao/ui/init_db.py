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
import psycopg2
import psycopg2.errors
from psycopg2.sql import SQL, Identifier, Placeholder

from ..qgis_plugin_tools.tools.resources import load_ui

from qgis.core import QgsApplication, QgsProject, QgsAuthManager, QgsAuthMethodConfig
from qgis.utils import iface

from PyQt5 import QtGui
from PyQt5.QtCore import QSettings
from PyQt5.QtWidgets import QDialog, QWidget

from ..core.exceptions import InitializationCancelled, UnableToDropDatabase, UnableToConnectToDb, ProjectInInvalidFormat
from ..db.db_utils import get_existing_database_connections, get_db_connection_params, set_auth_cfg, fix_data_sources_from_binary_projects
from ..ui.ask_password import DbAskPasswordDialog
from ..ui.ask_credentials import DbAskCredentialsDialog
from ..ui.ask_permission import DbAskPermissionDialog
from ..qgis_plugin_tools.tools.custom_logging import bar_msg
from ..qgis_plugin_tools.tools.i18n import tr
from ..qgis_plugin_tools.tools.network import fetch
from ..qgis_plugin_tools.tools.resources import load_ui, plugin_name, resources_path

#from ..qgis_plugin_tools.tools.settings import get_setting

FORM_CLASS = load_ui('db_init.ui')
LOGGER = logging.getLogger(plugin_name())

INFRAO_ADMIN = 'infrao_admin'

class Dialog(QDialog, FORM_CLASS):
    
    def __init__(self, iface, parent=None):
        QDialog.__init__(self, parent)
        self.setupUi(self)
        self.iface = iface
        self.is_running = False
        
        self.populate_dbComboBox()

        self.closeButton.clicked.connect(self.close)
        self.agreedCheckBox.clicked.connect(self.enable_init_button)
        self.btnDbInitialize.setEnabled(self.agreedCheckBox.isChecked())
        self.btnDbInitialize.clicked.connect(self.init_database)
        self.openProjButton.clicked.connect(self.open_project)
        self.refreshProjButton.clicked.connect(self.populate_projectComboBox)
        

    def init_database(self):
        selected_db = self.dbComboBox.currentText()
        if selected_db == "":
            iface.messageBar().pushMessage("Tietokantayhteyttä ei ole valittu.", level=2, duration=5)
            return
        conn_params = get_db_connection_params(selected_db)
        LOGGER.info(f"ATTEMPTING TO INITIALIZE {selected_db}")
        if (conn_params['password'] ==  None) or (conn_params ['user'] == None):
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


        db_found = self.check_existing_db(conn_params)
        if db_found == None:
            return
        if (db_found):
            iface.messageBar().pushMessage("InfraO- tietokanta löytyi jo palvelimelta. Uudelleenalustus vaatii tietokannan poistamisen.", level=2, duration=5)
            return
        if not (db_found):
            new_pwd = self.ask_new_password()
            if new_pwd == "":
                iface.messageBar().pushMessage("Ei voi jatkaa ilman salasanaa.", level=2, duration=5)
                return
            conn_params["dbname"] = 'postgres'
            self.create_db(conn_params, new_pwd)
            self.check_postgis(conn_params)
            self.run_sql(new_pwd, conn_params, selected_db)
            self.add_project(new_pwd)

    
    def check_existing_db(self, conn_params):
        LOGGER.info("Checking for existing InfraO database.")
        try:
            with(psycopg2.connect(**conn_params)) as conn:
                conn.autocommit = True
                with conn.cursor() as curs:
                    curs.execute("select * from pg_database;")
                    check_db = curs.fetchall()
                    db_found = any('infrao' in word for word in check_db)
                    LOGGER.info("InfraO database found." if (db_found) else "InfraO database not found.")
            return db_found
        except psycopg2.OperationalError:
            self.db_connection_msg()
            LOGGER.warning("Unable to connect to database.")
            return
        

    def create_db(self, conn_params, password):
        #Old way of connecting used to avoid a psycopg2 error when running CREATE DATABASE command in newer psycopg2 versions (which QGIS uses on Linux)
        try:
            conn = psycopg2.connect(**conn_params)
            conn.autocommit = True
            with conn.cursor() as curs:
                LOGGER.info("Creating InfraO database and infrao_admin role.")

                query_droprole = SQL('DROP ROLE IF EXISTS {}').format(Identifier(INFRAO_ADMIN))
                curs.execute(query_droprole)

                query_createrole = SQL('CREATE ROLE {} WITH PASSWORD {} CREATEROLE LOGIN').format(Identifier(INFRAO_ADMIN), Placeholder())
                curs.execute(query_createrole, (password,))

                query_grant = SQL('GRANT {} TO {}').format(Identifier(INFRAO_ADMIN), Identifier('postgres'))
                curs.execute(query_grant)

                query_createdb = SQL('CREATE DATABASE {} OWNER={} TABLESPACE=ts_infrao').format(Identifier('infrao'), Identifier(INFRAO_ADMIN)) #TODO: tablespace
                curs.execute(query_createdb)
                
        except psycopg2.OperationalError:
            self.db_connection_msg()
            return
        finally:
            if conn:
                conn.close()


    def run_sql(self, pwd, conn_params, dbname):
        LOGGER.info("Connecting to InfraO database and creating PostGIS extension if it doesn't exist.")
        conn_params["dbname"] = 'infrao'
        with(psycopg2.connect(**conn_params)) as conn:
            conn.autocommit = True
            with conn.cursor() as curs:
                curs.execute("CREATE EXTENSION IF NOT EXISTS postgis;")
        conn_params["user"] = 'infrao_admin'
        conn_params["password"] = pwd
        LOGGER.info("Attempting to connect to InfraO database.")
        try:
            with(psycopg2.connect(**conn_params)) as conn:
                conn.autocommit = True
                with conn.cursor() as curs:
                    try:
                        LOGGER.info("Attempting to read sql file.")
                        with open(resources_path('V1.0.0__initial.sql'), "r") as f:
                            LOGGER.info("File opened.")
                            curs.execute(f.read())
                            LOGGER.info("Refreshing list of connections.")
                            settings = QSettings()
                            root_path = f'PostgreSQL/connections/{dbname}'
                            #settings.value()
                            settings.setValue(f'{root_path}/database', conn_params.get('dbname'))
                            settings.setValue(f'{root_path}/username', 'infrao_admin')
                            settings.setValue(f'{root_path}/password', conn_params.get(pwd))
                            iface.mainWindow().findChildren(QWidget, 'Browser')[0].refresh()
                            iface.messageBar().pushMessage(dbname, "-tietokanta alustettu onnistuneesti.", level=3, duration=5)
                            #self.close()

                    except Exception as e:
                        LOGGER.info(resources_path('V1.0.0__initial.sql'))
                        LOGGER.info("Reading sql file failed.")
                        LOGGER.info(e)
        except:
            LOGGER.info("Unable to connect to database.")
            self.db_connection_msg()
            return

    
    def add_project(self, pwd):
        selected_db = self.dbComboBox.currentText()
        conn_params = get_db_connection_params(selected_db)
        
        LOGGER.info("Adding project")
        f = open(resources_path('infrao_tyotila.sql'), 'r', encoding='utf-16')
        content = f.read()
        f.close()
        proj_bytes = [line.split(',')[5][4:-3] for line in content.split('\n') if
                    line.startswith('INSERT INTO public.qgis_projects')]
        byts = [bytes.fromhex(b) for b in proj_bytes]
        ret_vals = fix_data_sources_from_binary_projects(conn_params, auth_cfg_id=selected_db, contents=byts)
        for i in range(len(proj_bytes)):
            content = content.replace(proj_bytes[i], ret_vals[i].decode('utf-8'))
        set_auth_cfg(selected_db,selected_db,'infrao_admin',pwd)
        conn_params["dbname"] = 'infrao'
        conn_params["user"] = 'infrao_admin'###
        conn_params["password"] = pwd###

        try:
            with(psycopg2.connect(**conn_params)) as conn:
                conn.autocommit = True
                with conn.cursor() as curs:
                    curs.execute(content)
        except psycopg2.errors.OperationalError:
            self.db_connection_msg()
            LOGGER.info("Unable to connect to database.")
            return

        self.populate_projectComboBox()
        
   
    def enable_init_button(self):
        self.btnDbInitialize.setEnabled(self.agreedCheckBox.isChecked())


    def populate_dbComboBox(self):
        self.dbComboBox.clear()
        connections = get_existing_database_connections()
        for conn in connections:
            self.dbComboBox.addItem(conn)


    def open_project(self):
        selected_db = self.dbComboBox.currentText()
        projectname=self.projectComboBox.currentText()
        LOGGER.info(projectname)
        if projectname == None or projectname == "":
            iface.messageBar().pushMessage("Työtilaa ei ole valittu.", level=2, duration=5)
            return
        conn_params = get_db_connection_params(selected_db)
        user = conn_params['user']
        password = conn_params['password']
        auth_mgr: QgsAuthManager = QgsApplication.authManager()
        if selected_db in auth_mgr.availableAuthMethodConfigs().keys():
            config = QgsAuthMethodConfig()
            auth_mgr.loadAuthenticationConfig(selected_db, config, True)
            user = config.config('username')
            password = config.config('password')

        if (password ==  None) or (user == None):
                LOGGER.info("No username and/or password found.")
                ask_credentials_dlg = DbAskCredentialsDialog()
                result = ask_credentials_dlg.exec_()
                if (result):
                    user = ask_credentials_dlg.userLineEdit.text()
                    password = ask_credentials_dlg.pwdLineEdit.text()
                else:
                    iface.messageBar().pushMessage("Ei voi avata ilman käyttäjänimeä tai salasanaa.", level=1, duration=5)
                    return

        host=conn_params['host']
        port=conn_params['port']
        sslmode = 'disable'
        dbname=conn_params['dbname']
        schema='public'
        
        uri = f'postgresql://{user}:{password}@{host}:{port}?&dbname={dbname}&schema={schema}&project={projectname}'
        QgsProject.instance().read(uri)
        LOGGER.info(f"Open project {self.projectComboBox.currentText()}")

    
    def populate_projectComboBox(self):
        selected_db = self.dbComboBox.currentText()
        if selected_db == "":
            iface.messageBar().pushMessage("Tietokantayhteyttä ei ole valittu.", level=2, duration=5)
            return
        conn_params_ = get_db_connection_params(selected_db)
        conn_params_['dbname'] = "infrao"
        conn_params = self.get_auth_parameters(conn_params_, selected_db)

        if (conn_params['password'] ==  None) or (conn_params ['user'] == None):
                LOGGER.info("No username and/or password found.")
                ask_credentials_dlg = DbAskCredentialsDialog()
                result = ask_credentials_dlg.exec_()
                if (result):
                    conn_params['user'] = ask_credentials_dlg.userLineEdit.text()
                    conn_params['password'] = ask_credentials_dlg.pwdLineEdit.text()
                else:
                    iface.messageBar().pushMessage("Ei voi päivittää ilman käyttäjänimeä tai salasanaa.", level=1, duration=5)
                    return
        try:
            with psycopg2.connect(**conn_params) as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT name FROM qgis_projects;")
                    available_projects = cur.fetchall()
        except psycopg2.OperationalError:
            self.db_connection_msg()
            return
        except psycopg2.errors.UndefinedTable:
            iface.messageBar().pushMessage("Työtilaa ei löytynyt tietokannasta.", level=1, duration=5)
            return
        projects = [proj[0] for proj in available_projects]

        self.projectComboBox.clear()
        self.projectComboBox.addItems(projects)


    def check_postgis(self, conn_params):
        try:
            with(psycopg2.connect(**conn_params)) as conn:
                conn.autocommit = True
                with conn.cursor() as curs:
                    LOGGER.info('Checking for PostGIS extension.')
                    curs.execute("select extname from pg_extension;")
                    check_ext = curs.fetchall()
                    postgis_found = any('postgis' in word for word in check_ext)
                    LOGGER.info("PostGIS extension found." if (postgis_found) else "PostGIS extension not found.")
                    if not (postgis_found):
                        LOGGER.info("Attempting to create extension postgis.")
                        try:
                            curs.execute("create extension postgis;")
                        except psycopg2.errors.FeatureNotSupported as exception:
                            LOGGER.warning("Unable to create extension.")
                            LOGGER.warning(exception)
        except psycopg2.OperationalError:
            self.db_connection_msg()
            LOGGER.warning("Unable to connect to database.")
            return
            



    def ask_new_password(self):
        ask_password_dlg = DbAskPasswordDialog()
        ask_password_dlg.exec_()
        return ask_password_dlg.result_
    

    def db_connection_msg(self):
        iface.messageBar().pushMessage("Yhteys tietokantaan epäonnistui.", level=2, duration=5)


    def get_auth_parameters(self, conn_params, selected_db):
        auth_mgr: QgsAuthManager = QgsApplication.authManager()
        if selected_db in auth_mgr.availableAuthMethodConfigs().keys():
            config = QgsAuthMethodConfig()
            auth_mgr.loadAuthenticationConfig(selected_db, config, True)
            conn_params['user'] = config.config('username')
            conn_params['password'] = config.config('password')
        return conn_params
        