from qgis.PyQt import QtWidgets

from ..qgis_plugin_tools.tools.resources import load_ui

FORM_CLASS = load_ui('ask_permission_dialog.ui')


class DbAskPermissionDialog(QtWidgets.QDialog, FORM_CLASS):
    onCloseHandler = None

    def __init__(self, text, parent=None):
        """Constructor."""

        # noinspection PyArgumentList
        super(DbAskPermissionDialog, self).__init__(parent)
        self.setupUi(self)
        self.permissionLabel.setText(text)