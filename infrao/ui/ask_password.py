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
