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

from qgis.PyQt import QtWidgets

from ..qgis_plugin_tools.tools.resources import load_ui

FORM_CLASS = load_ui('ask_password_dialog.ui')


class DbAskPasswordDialog(QtWidgets.QDialog, FORM_CLASS):
    onCloseHandler = None

    result_ = ""

    def __init__(self, parent=None):
        """Constructor."""

        # noinspection PyArgumentList
        super(DbAskPasswordDialog, self).__init__(parent)
        self.setupUi(self)

        self.okButton.clicked.connect(self.check_match)
        self.closeButton.clicked.connect(self.close_self)



    def check_match(self):
        if len(self.pwdLineEdit.text()) <= 8:
            self.pwdNoMatchLabel.setText("Salasanan pitää olla vähintään 8 merkkiä pitkä.")
        elif not (self.pwdLineEdit.text() == self.pwd2LineEdit.text()):
            self.pwdNoMatchLabel.setText("Salasanat eivät täsmää.")
        else:
            self.result_ = self.pwdLineEdit.text()
            self.close()
        

    def close_self(self):
        self.result_ = ""
        self.close()
