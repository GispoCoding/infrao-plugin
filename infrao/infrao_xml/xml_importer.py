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

from ..qgis_plugin_tools.tools.resources import plugin_name, load_ui
from qgis.core import QgsProject
from qgis.utils import iface

from ..ui.init_db import Dialog as DLG
from ..db.db_utils import get_db_connection_params
from ..ui.ask_credentials import DbAskCredentialsDialog

from xml.etree import ElementTree as ET

from PyQt5.QtWidgets import QDialog, QFileDialog

from .xml_tools.import_tools import xml_import


FORM_CLASS = load_ui('import.ui')
LOGGER = logging.getLogger(plugin_name())

class ImportDialog(QDialog, FORM_CLASS):
    def __init__(self, iface, parent=None):
        QDialog.__init__(self, parent)
        self.setupUi(self)
        self.iface = iface
        self.is_running = False
        
        DLG.populate_dbComboBox(self)

        self.closeButton.clicked.connect(self.close)
        self.filePathButton.clicked.connect(self.get_file_path)
        self.importButton.clicked.connect(self.execute)
        #self.filePathLineEdit.setText("") # Fill in a file path for quick testing

    
    def get_file_path(self):
        open_file, _ = QFileDialog.getOpenFileName(None, "Open File", "", "GML or XML Files (*.gml; *.xml)")
        self.filePathLineEdit.setText(open_file)

    
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
        open_file = self.filePathLineEdit.value()

        tree = ET.parse(open_file)
        try:
            xml_import(conn_params, tree, False)
        except FileNotFoundError:
            iface.messageBar().pushMessage("Virheellinen tiedostopolku. Tietoja ei voitu tuoda.", level=1, duration=5)
        except PermissionError:
            iface.messageBar().pushMessage("Pääsy estetty hakemistoon. Tarkista tiedoston polku.", level=1, duration=5)