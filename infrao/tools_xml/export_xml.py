from xml.dom import minidom
#import xml.etree.ElementTree as etr
import psycopg2 as psy2

from qgis.core import QgsProject, QgsVectorLayer, QgsFeatureRequest, QgsFeature
from qgis.utils import iface

from PyQt5.QtCore import QCoreApplication

class XMLExporter:
    def __init__(self, qgs_app: QCoreApplication) -> None:
        self.qgs_app = qgs_app

    def export_xml(self):
        print("XML EXPORTED")