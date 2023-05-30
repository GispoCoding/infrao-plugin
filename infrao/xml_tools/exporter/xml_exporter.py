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

from PyQt5.QtCore import QDate
from PyQt5.QtWidgets import QDialog, QFileDialog, QDateEdit, QComboBox, QMessageBox
from qgis.core import QgsExpressionContextUtils, NULL
from qgis.utils import iface

from ...ui.init_db import Dialog as DLG
from ...db.db_utils import get_db_connection_params
from ...ui.ask_credentials import DbAskCredentialsDialog

from ...qgis_plugin_tools.tools.resources import plugin_name, load_ui
from ..export_tools import AINEISTO_TILA, INFRAO_AINEISTOTOIMITUKSEN_TIEDOT, xml_export


FORM_CLASS = load_ui('export.ui')
LOGGER = logging.getLogger(plugin_name())

class ExportDialog(QDialog, FORM_CLASS):
    def __init__(self, iface, parent=None):
        QDialog.__init__(self, parent)
        self.setupUi(self)
        self.iface = iface
        self.is_running = False
        
        DLG.populate_dbComboBox(self)

        self.export_shipment_information = True

        self.closeButton.clicked.connect(self.close)
        self.filePathButton.clicked.connect(self.get_file_path)
        self.exportButton.clicked.connect(self.execute)
        self.filePathLineEdit.setText("C:/Users/juho-/Desktop/testi.gml") # Fill in a file path for quick testing
        self.exportShipmentInformation.clicked.connect(self.shipment_information_export_clicked)

        self.shipment_information = {}

        self.tt_toimituspvm.setDate(QDate.currentDate())
        user_name = QgsExpressionContextUtils.globalScope().variable('user_full_name')
        if user_name:
            self.tt_aineistotoimittaja.setText(user_name)

        for value in AINEISTO_TILA:
            self.tt_tila.addItem(value)

    
    def shipment_information_export_clicked(self):
        self.export_shipment_information = not self.exportShipmentInformation.isChecked()
        for key in INFRAO_AINEISTOTOIMITUKSEN_TIEDOT.keys():
            widget = getattr(self, "tt_" + key)
            widget.setEnabled(self.export_shipment_information)
    

    def get_file_path(self):
        save_file, _ = QFileDialog.getSaveFileName(None, "Save File", "", "GML Files (*.gml)")
        if save_file:
            if not save_file.endswith('.gml'):
                save_file += '.gml'
        self.filePathLineEdit.setText(save_file)

    
    def execute(self):
        if self.export_shipment_information:
            for idx, key in enumerate(INFRAO_AINEISTOTOIMITUKSEN_TIEDOT.keys()):
                widget = getattr(self, "tt_" + key)
                if isinstance(widget, QComboBox):
                    value = widget.currentText()
                elif isinstance(widget, QDateEdit):
                    value = widget.date()
                    value = value.toString("yyyy-MM-dd")
                else:
                    value = widget.text()

                if value == '':
                    value = None

                if idx < 6 and value == None:
                    message_box = QMessageBox()
                    message_box.setWindowTitle("Virhe")

                    error_message = "Täytä kaikki pakolliset tiedot."

                    message_box.setText(error_message)
                    message_box.setIcon(QMessageBox.Warning)
                    message_box.setStandardButtons(QMessageBox.Ok)
                    message_box.exec_()

                    return

                self.shipment_information[key] = value

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
            
        save_file = self.filePathLineEdit.value()

        try:
            xml_export(conn_params, save_file, self.shipment_information)
            self.shipment_information = {}
            iface.messageBar().pushMessage(f"Tiedosto tallennettu polkuun: {save_file}", level=3, duration=10)
        except FileNotFoundError:
            iface.messageBar().pushMessage("Virheellinen tiedostopolku. Tiedostoa ei voitu tallentaa", level=1, duration=5)
        except PermissionError:
            iface.messageBar().pushMessage("Pääsy estetty hakemistoon. Tarkista tallennuspolku.", level=1, duration=5)