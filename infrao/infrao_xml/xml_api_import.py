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
import requests
import traceback

from xml.etree import ElementTree as ET

from ..qgis_plugin_tools.tools.settings import parse_value
from ..qgis_plugin_tools.tools.resources import plugin_name, load_ui
from qgis.core import QgsProject
from qgis.utils import iface

from ..ui.init_db import Dialog as DLG
from ..db.db_utils import get_db_connection_params
from ..ui.ask_credentials import DbAskCredentialsDialog

from PyQt5.QtWidgets import QDialog, QFileDialog
from PyQt5.QtCore import QSettings

from .xml_tools.import_tools import xml_import

FORM_CLASS = load_ui('import_api.ui')
LOGGER = logging.getLogger(plugin_name())

class ImportFromApiDialog(QDialog, FORM_CLASS):
    def __init__(self, iface, parent=None):
        QDialog.__init__(self, parent)
        self.setupUi(self)
        self.iface = iface
        self.is_running = False
        
        DLG.populate_dbComboBox(self)
        self.populate_apiComboBox()
        self.populate_layerComboBox()

        self.closeButton.clicked.connect(self.close)
        self.importButton.clicked.connect(self.execute)
        self.apiComboBox.currentTextChanged.connect(self.populate_layerComboBox)
        #self.filePathLineEdit.setText("") # Fill in a file path for quick testing

    def get_layer_gml(self): # TODO: what if bad response
        ogc_api_url = self.get_connection_url()

        if ogc_api_url is None:
            return None

        selected_layer = self.layerComboBox.currentText()

        if not selected_layer.startswith("infrao:"):
            iface.messageBar().pushMessage("Taso ei ole Infra-O taso.", level=1, duration=5)
            return None

        gml_url = f"{ogc_api_url}collections/{selected_layer}/items?f=application%2Fgml%2Bxml;version=3.2"

        response = requests.get(gml_url)

        layer_gml = response.text
        return layer_gml
    

    def get_connection_url(self): # TODO: what if no connections
        connection_name = self.apiComboBox.currentText()

        if connection_name == "<ei yhteyksiä>":
            iface.messageBar().pushMessage("OGC API Features- yhteyksiä ei löytynyt.", level=1, duration=5)
            return None

        s = QSettings()
        s.beginGroup(f"qgis/connections-wfs/{connection_name}")

        ogc_api_url = parse_value(s.value("url"))

        s.endGroup()

        return ogc_api_url


    def populate_layerComboBox(self): # TODO: what if no connections
        self.layerComboBox.clear()

        ogc_api_url = self.get_connection_url()

        if ogc_api_url is None:
            iface.messageBar().pushMessage("OGC API Features- yhteyksiä ei löytynyt.", level=1, duration=5)
            return

        ogc_api_url = ogc_api_url[:-1] if ogc_api_url.endswith('/') else ogc_api_url

        collections_url = f'{ogc_api_url}/collections/'

        try:
            response = requests.get(collections_url)
        except:
            msg = traceback.format_exc()
            LOGGER.info(msg)
            iface.messageBar().pushMessage("Yhteys OGC API Features- rajapintaan ei onnistunut. Tarkista linkki.", level=1, duration=5)
            return

        layers = set()

        if response.status_code == 200:
            collections = response.json().get('collections', [])
            for collection in collections:
                layer_name = collection.get('id')
                layers.add(layer_name)
        else:
            iface.messageBar().pushMessage("Tasoja ei löytynyt. Tarkista linkki.", level=1, duration=5)
            self.layerComboBox.addItem("<ei tasoja>")

        for layer in layers:
            self.layerComboBox.addItem(layer)


    def populate_apiComboBox(self):
        s = QSettings()
        s.beginGroup("qgis/connections-wfs")
        keys = s.allKeys()
        s.endGroup()
        connections = {key.split('/')[0] for key in keys if '/' in key}
        if not connections:
            self.apiComboBox.addItem("<ei yhteyksiä>")
        for conn in connections:
            self.apiComboBox.addItem(conn)

    
    def execute(self):
        conn_params = get_db_connection_params(self.dbComboBox.currentText())
        if (conn_params['password'] ==  None) or (conn_params ['user'] == None):
            LOGGER.info("No username and/or password found.")
            ask_credentials_dlg = DbAskCredentialsDialog()
            result = ask_credentials_dlg.exec_()
            if (result):
                conn_params['user'] = ask_credentials_dlg.userLineEdit.text()
                conn_params['password'] = ask_credentials_dlg.pwdLineEdit.text()
            else:
                ask_credentials_dlg.close()
                iface.messageBar().pushMessage("Ei voi viedä ilman käyttäjänimeä tai salasanaa.", level=1, duration=5)
                return
            
        gml_string = self.get_layer_gml()

        if gml_string is not None:
            tree = ET.ElementTree(ET.fromstring(gml_string))

            try:
                xml_import(conn_params, tree, True)
            except FileNotFoundError:
                iface.messageBar().pushMessage("Virheellinen tiedostopolku. Tietoja ei voitu tuoda.", level=1, duration=5)
            except PermissionError:
                iface.messageBar().pushMessage("Pääsy estetty hakemistoon. Tarkista tiedoston polku.", level=1, duration=5)