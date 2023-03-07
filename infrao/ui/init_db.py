import logging
import psycopg2
import psycopg2.errors
import os

from ..qgis_plugin_tools.tools.resources import load_ui

from qgis.core import QgsApplication
from qgis.utils import iface

from PyQt5 import QtGui
from PyQt5.QtCore import QSettings
from PyQt5.QtWidgets import QDialog, QWidget

from ..core.exceptions import InitializationCancelled, UnableToDropDatabase, UnableToConnectToDb
from ..db.db_utils import get_existing_database_connections, get_db_connection_params
from ..ui.ask_password import DbAskPasswordDialog
from ..ui.ask_credentials import DbAskCredentialsDialog
from ..ui.ask_permission import DbAskPermissionDialog
from ..qgis_plugin_tools.tools.custom_logging import bar_msg
from ..qgis_plugin_tools.tools.i18n import tr
from ..qgis_plugin_tools.tools.resources import load_ui, plugin_name
from ..qgis_plugin_tools.tools.settings import get_setting

FORM_CLASS = load_ui('db_init.ui')
LOGGER = logging.getLogger(plugin_name())

class Dialog(QDialog, FORM_CLASS):
    
    def __init__(self, iface, parent=None):
        QDialog.__init__(self, parent)
        self.setupUi(self)
        QWidget.setWindowTitle(self, "Initialize database")
        self.iface = iface
        self.is_running = False
        
        self.populate_dbComboBox()

        self.closeButton.clicked.connect(self.close)
        self.btnDbInitialize.clicked.connect(self.init_database)
        

    def init_database(self):
        agreed = self.agreedCheckBox.isChecked()
        if (agreed):
            selected_db = self.dbComboBox.currentText()
            conn_params = get_db_connection_params(selected_db)
            LOGGER.info(f"ATTEMPTING TO INITIALIZE {selected_db}")
            if (conn_params['password'] ==  None) or (conn_params ['user'] == None):
                ask_credentials_dlg = DbAskCredentialsDialog()
                result = ask_credentials_dlg.exec_()
                if (result):
                    conn_params['user'] = ask_credentials_dlg.userLineEdit.text()
                    conn_params['password'] = ask_credentials_dlg.pwdLineEdit.text()
                else:
                    raise InitializationCancelled("Canceling",bar_msg("Cannot initialize without username and password."))
            try:
                db_found = self.check_existing_db(conn_params)
                if (db_found):
                    db_found = self.drop_db(conn_params)
                if not (db_found):
                    pwd = self.create_db(conn_params)
                    self.run_sql(pwd, conn_params, selected_db)
            except psycopg2.OperationalError:
                LOGGER.warning("Unable to connect to database.")
                pass
            LOGGER.info("INITIALIZATION ENDED")

    
    def check_existing_db(self, conn_params):
        with(psycopg2.connect(**conn_params)) as conn:
            conn.autocommit = True
            with conn.cursor() as curs:
                LOGGER.info("Checking for infrao database.")
                curs.execute("select * from pg_database;")
                check_db = curs.fetchall()
                db_found = any('infrao' in word for word in check_db)
                LOGGER.info("Database infrao found." if (db_found) else "Database infrao not found.")
        return db_found


    def drop_db(self, conn_params):
        conn_params['dbname'] = 'postgres'
        try:
            with(psycopg2.connect(**conn_params)) as conn:
                conn.autocommit = True
                with conn.cursor() as curs:
                    ask_permission_dlg_1 = DbAskPermissionDialog("A database called InfraO already exists in this PostGIS server.\nIf you continue the database and all data therein will be deleted.\nDo you wish to proceed?")
                    result_1 = ask_permission_dlg_1.exec_()
                    if result_1:
                        ask_permission_dlg_2 = DbAskPermissionDialog("Are you sure?")
                        result_2 = ask_permission_dlg_2.exec_()
                        if result_2:
                            try:
                                LOGGER.info("Trying to drop database.")
                                curs.execute("DROP DATABASE infrao WITH (FORCE);")
                                db_found = False
                            except:
                                LOGGER.info("Unable to drop database.")
                                raise UnableToDropDatabase
        except:
            raise UnableToConnectToDb
        return db_found

    def create_db(self, conn_params):
        try:
            with(psycopg2.connect(**conn_params)) as conn:
                conn.autocommit = True
                with conn.cursor() as curs:
                    ask_password_dlg = DbAskPasswordDialog()
                    ask_password_dlg.exec_()
                    ask_password_dlg.close()
                    password = ask_password_dlg.pwdLineEdit.text()
                    curs.execute("DROP ROLE IF EXISTS infrao_admin;")
                    curs.execute(f"CREATE ROLE infrao_admin WITH PASSWORD '{password}' CREATEROLE LOGIN;")
                    curs.execute("CREATE DATABASE infrao TABLESPACE=pg_default OWNER=infrao_admin;")
                    LOGGER.info('Checking for PostGIS extension.')
                    curs.execute("select * from pg_extension;")
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
        except:
            raise UnableToConnectToDb
        return password


    def run_sql(self, pwd, conn_params, dbname):
        #LOGGER.info(pwd, conn_params)
        conn_params["dbname"] = 'infrao'
        with(psycopg2.connect(**conn_params)) as conn:
            conn.autocommit = True
            with conn.cursor() as curs:
                curs.execute("CREATE EXTENSION IF NOT EXISTS postgis;")
        conn_params["user"] = 'infrao_admin'
        conn_params["password"] = pwd
        try:
            with(psycopg2.connect(**conn_params)) as conn:
                database = conn_params.get('dbname')
                LOGGER.info(f'Connected to database {database}.')
                conn.autocommit = True
                with conn.cursor() as curs:
                    try:
                        with open(f"{os.path.abspath(os.path.join(os.path.dirname( __file__ ), os.pardir, 'resources'))}\V1.0.0__initial.sql", "r") as f:
                            LOGGER.info("File opened.")
                            curs.execute(f.read())
                            settings = QSettings()
                            root_path = f'PostgreSQL/connections/{dbname}'
                            #settings.value()
                            settings.setValue(f'{root_path}/database', conn_params.get('dbname'))
                            settings.setValue(f'{root_path}/username', conn_params.get('infrao_admin'))
                            settings.setValue(f'{root_path}/password', conn_params.get(pwd))
                            iface.mainWindow().findChildren(QWidget, 'Browser')[0].refresh()

                    except Exception as e:
                        LOGGER.info(f"{os.path.abspath(os.path.join(os.path.dirname( __file__ ), os.pardir, 'resources'))}\V1.0.0__initial.sql")
                        LOGGER.info("Reading sql file failed.")
                        LOGGER.info(e)
        except:
            LOGGER.info("New connection to database failed.")
            pass

    def populate_dbComboBox(self):
        self.dbComboBox.clear()
        connections = get_existing_database_connections()
        for conn in connections:
            self.dbComboBox.addItem(conn)