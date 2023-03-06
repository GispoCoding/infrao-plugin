from qgis.PyQt import QtWidgets

from ..qgis_plugin_tools.tools.resources import load_ui
FORM_CLASS = load_ui('ask_password_dialog.ui')


class DbAskPasswordDialog(QtWidgets.QDialog, FORM_CLASS):
    onCloseHandler = None

    def __init__(self, parent=None):
        """Constructor."""

        # noinspection PyArgumentList
        super(DbAskPasswordDialog, self).__init__(parent)
        self.setupUi(self)

        self.cancelButton.clicked.connect(self.close)
        self.okButton.clicked.connect(self.check_match)


    def check_match(self):
        if len(self.pwdLineEdit.text()) <= 8:
            self.pwdNoMatchLabel.setText("Password has to be at least 8 characters long.")
        elif not (self.pwdLineEdit.text() == self.pwd2LineEdit.text()):
            self.pwdNoMatchLabel.setText("Passwords do not match.")
        else:
            self.close()