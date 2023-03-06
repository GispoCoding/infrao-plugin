from qgis.PyQt import QtWidgets

from ..qgis_plugin_tools.tools.resources import load_ui

FORM_CLASS = load_ui('ask_credentials_dialog.ui')


class DbAskCredentialsDialog(QtWidgets.QDialog, FORM_CLASS):
    onCloseHandler = None

    def __init__(self, parent=None):
        """Constructor."""

        # noinspection PyArgumentList
        super(DbAskCredentialsDialog, self).__init__(parent)
        self.setupUi(self)
        
        self.userLineEdit.setText("postgres")