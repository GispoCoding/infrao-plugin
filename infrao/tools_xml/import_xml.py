import xml.etree.ElementTree as ET

from qgis.core import QgsProject, QgsFeature, QgsGeometry, QgsPointXY

from PyQt5.QtCore import QCoreApplication

class XMLImporter:
    def __init__(self, qgs_app: QCoreApplication) -> None:
        self.qgs_app = qgs_app
    

    def import_xml(self, f):
        f = "XML Imported successfully"
        return f