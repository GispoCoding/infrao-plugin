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