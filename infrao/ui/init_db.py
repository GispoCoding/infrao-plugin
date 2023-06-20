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
import traceback

import logging
import psycopg2
import psycopg2.errors

from ..qgis_plugin_tools.tools.resources import load_ui

from qgis.core import QgsApplication, QgsProject, QgsAuthManager, QgsAuthMethodConfig
from qgis.utils import iface

from PyQt5.QtWidgets import QDialog

from ..db.db_utils import get_existing_database_connections, get_db_connection_params, set_auth_cfg, fix_data_sources_from_binary_projects
from ..ui.ask_credentials import DbAskCredentialsDialog
from ..qgis_plugin_tools.tools.resources import load_ui, plugin_name, resources_path

FORM_CLASS = load_ui('db_init.ui')
LOGGER = logging.getLogger(plugin_name())

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
        try:
            database_created = self.run_sql(conn_params, selected_db)
        except:
            iface.messageBar().pushMessage("Virhe tietokantarakenteen luomisessa. Katso viestilokista lisätietoja.", level=2, duration=5)
            error_msg = traceback.format_exc()
            LOGGER.info(error_msg)
            return
        if database_created == True:
            try:
                self.add_project(conn_params)
            except:
                iface.messageBar().pushMessage("Virhe QGIS- projektin lisäämisessä tietokantaan. Katso viestilokista lisätietoja.", level=2, duration=5)
                error_msg = traceback.format_exc()
                LOGGER.info(error_msg)
                return


    def run_sql(self, conn_params, dbname):
        LOGGER.info("Attempting to connect to database.")
        try:
            with(psycopg2.connect(**conn_params)) as conn:
                conn.autocommit = True
                with conn.cursor() as curs:
                    try:
                        LOGGER.info("Attempting to read sql file.")
                        with open(resources_path('V1.0.0__initial.sql'), "r") as f:
                            LOGGER.info("File opened.")
                            lines = f.readlines()
                            modified_script = ''
                            for line in lines:
                                if 'ALTER' in line and 'OWNER TO' in line:
                                    continue
                                modified_script +=line
                            curs.execute(modified_script)
                            iface.messageBar().pushMessage(dbname, "-tietokanta alustettu onnistuneesti.", level=3, duration=5)
                            return True
                            #self.close()
                    except psycopg2.errors.InsufficientPrivilege:
                        iface.messageBar().pushMessage("Käyttäjällä ei riittäviä oikeuksia lisätä skeemoja, tauluja, sekvenssejä tai PostGIS- liitännäistä. Katso viestilokista lisätietoja.", level=2, duration=5)
                        error_msg = traceback.format_exc()
                        LOGGER.info(error_msg)
                        if '"postgis"' in error_msg:
                            LOGGER.info("Lisää tarvittavat oikeudet liitännäisen lisäämiseen käyttäjälle, tai lisää PostGIS- liitännäiseen tietokantaan etukäteen.")
                    except Exception as error:
                        iface.messageBar().pushMessage("Virhe tietokantarakenteen luomisessa. Katso viestilokista lisätietoja.", level=2, duration=5)
                        LOGGER.info(resources_path('V1.0.0__initial.sql'))
                        LOGGER.info("Reading sql file failed.")
                        error_msg = traceback.format_exc()
                        LOGGER.info(error_msg)
                        return False
        except:
            LOGGER.info("Unable to connect to database.")
            self.db_connection_msg()
            return False

    
    def add_project(self, conn_params):
        selected_db = self.dbComboBox.currentText()

        if selected_db == "":
            iface.messageBar().pushMessage("Tietokantayhteyttä ei ole valittu.", level=2, duration=5)
            return
        
        if conn_params == None:
            conn_params = get_db_connection_params(selected_db)
            if not conn_params['password'] or not conn_params['user']:
                LOGGER.info("No username and/or password found.")
                ask_credentials_dlg = DbAskCredentialsDialog()
                result = ask_credentials_dlg.exec_()
                if (result):
                    conn_params['user'] = ask_credentials_dlg.userLineEdit.text()
                    conn_params['password'] = ask_credentials_dlg.pwdLineEdit.text()
                else:
                    iface.messageBar().pushMessage("Ei voi päivittää ilman käyttäjänimeä tai salasanaa.", level=1, duration=5)
                    return
                        
        selected_db = self.dbComboBox.currentText()
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

        set_auth_cfg(selected_db,selected_db,conn_params['user'],conn_params['password'])

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
        conn_params = self.get_auth_parameters(conn_params_, selected_db)

        if not conn_params['password'] or not conn_params['user']:
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
                    cur.execute("SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'qgis_projects');")
                    table_exists = cur.fetchone()[0]
                    if table_exists:
                        cur.execute("SELECT name FROM qgis_projects;")
                        available_projects = cur.fetchall()
                    else:
                        available_projects = None
        except psycopg2.OperationalError:
            self.db_connection_msg()
            return
        except psycopg2.errors.UndefinedTable:
            iface.messageBar().pushMessage("Työtilaa ei löytynyt tietokannasta.", level=1, duration=5)
            return
        if available_projects is not None:
            projects = [proj[0] for proj in available_projects]

            self.projectComboBox.clear()
            self.projectComboBox.addItems(projects)
    

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
        