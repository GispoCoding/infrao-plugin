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
import xml.etree.ElementTree as ET
import psycopg2
from psycopg2.sql import SQL, Identifier
from psycopg2.extras import DictCursor

from re import sub, findall
from PyQt5.QtCore import QDateTime, Qt
from PyQt5.QtWidgets import QDialog, QFileDialog
from PyQt5.QtXml import QDomDocument
from qgis.core import QgsFeature, QgsProject, QgsOgcUtils, QgsGeometry, QgsPointXY, QgsWkbTypes,  NULL
from qgis.utils import iface

import time #TODO: remove

from ...ui.init_db import Dialog as DLG
from ...db.db_utils import get_db_connection_params
from ...ui.ask_credentials import DbAskCredentialsDialog

from ...qgis_plugin_tools.tools.resources import plugin_name, load_ui
from ..tools import (
    CORE_NS,
    INFRAO_KOHTEET,
    INFRAO_AJORATAMERKINTA,
    INFRAO_ERIKOISRAKENNEKERROS,
    INFRAO_HULEVESI,
    INFRAO_JATE,
    INFRAO_KALUSTE,
    INFRAO_KATUALUE,
    INFRAO_KATUALUEENOSA,
    INFRAO_KESKILINJA,
    INFRAO_LEIKKIVALINE,
    INFRAO_LIIKENNEMERKKI,
    INFRAO_LIIKUNTA,
    INFRAO_LIITE,
    INFRAO_MELU,
    INFRAO_MUUKASVI,
    INFRAO_MUUVARUSTE,
    INFRAO_NIMI,
    INFRAO_OPASTE,
    INFRAO_OSOITE,
    INFRAO_PAATOS,
    INFRAO_PUU,
    INFRAO_PYSAKOINTIRUUTU,
    INFRAO_RAKENNE,
    INFRAO_SIJAINTI,
    INFRAO_SUUNNITELMA,
    INFRAO_SUUNNITELMALINKKI,
    INFRAO_VIHERALUE,
    INFRAO_VIHERALUEENOSA,
    INFRAO_YMPARISTOTAIDE,
    INFRAO_AREA_ELEMENTS,
    INFRAO_ABSTRACT_PAIKKATIETOPALVELUKOHDE,
    INFRAO_ABSTRACT_VARUSTE,
    INFRAO_ABSTRACT_KASVILLISUUS,
    INFRAO_AJORATAMERKINTA_TAGS,
    INFRAO_ERIKOISRAKENNEKERROS_TAGS,
    INFRAO_HULEVESI_TAGS,
    INFRAO_INFRAOKOHTEET_TAGS,
    INFRAO_JATE_TAGS,
    INFRAO_KALUSTE_TAGS,
    INFRAO_KATUALUE_TAGS,
    INFRAO_KATUALUEENOSA_TAGS,
    INFRAO_KESKILINJA_TAGS,
    INFRAO_LEIKKIVALINE_TAGS,
    INFRAO_LIIKENNEMERKKI_TAGS,
    INFRAO_LIIKUNTA_TAGS,
    INFRAO_LIITE_TAGS,
    INFRAO_MELU_TAGS,
    INFRAO_MUUKASVI_TAGS,
    INFRAO_MUUVARUSTE_TAGS,
    INFRAO_NIMI_TAGS,
    INFRAO_OPASTE_TAGS,
    INFRAO_OSOITE_TAGS,
    INFRAO_PAATOS_TAGS,
    INFRAO_PUU_TAGS,
    INFRAO_PYSAKOINTIRUUTU_TAGS,
    INFRAO_RAKENNE_TAGS,
    INFRAO_SIJAINTI_TAGS,
    INFRAO_SUUNNITELMA_TAGS,
    INFRAO_SUUNNITELMALINKKI_TAGS,
    INFRAO_VIHERALUE_TAGS,
    INFRAO_VIHERALUEENOSA_TAGS,
    INFRAO_YMPARISTOTAIDE_TAGS,
    GML_POINT,
    GML_LINESTRING,
    GML_POLYGON,
    GML_EXTERIOR,
    GML_INTERIOR,
    GML_LINEAR_RING,
    GML_POS,
    GML_POS_LIST,
    GML_NULL,
    GML_ID,
    GML_FEATURE_MEMBERS,
    TIME_INSTANT,
    TIME_POSITION,
    TIME_PERIOD,
    BEGIN_POSITION,
    END_POSITION,
    REFERENCE_IDENTIFIER,
    TABLE_NAMES,
    ELEMENT_NAMES,
    SCHEMA_TABLE_NAMES,
    AREA_NAMES,
    AREA_INCLUDED_NAMES,
    INFRAO_DIFF_SIJAINTI_TAGS,
)

FORM_CLASS = load_ui('export.ui')
LOGGER = logging.getLogger(plugin_name())

def get_area_identifiers(conn_params):
    results_dicts = {"viheralueenosa": [],
                     "katualueenosa": [],
                     "viheralue": [],
                     "katualue": [],}
    with(psycopg2.connect(**conn_params)) as conn:
        with conn.cursor(cursor_factory=DictCursor) as curs:
            for key in results_dicts:
                if "osa" in key:
                    query = f"SELECT {key}.identifier, "
                    for i, (schema, table) in enumerate(TABLE_NAMES):#TODO: use psycopg2.SQL
                        if key == "viheralueenosa" and table == "keskilinja":
                            continue
                        else:
                            add_to_query = f"(SELECT array_agg({table}.identifier) FROM {schema}.{table} WHERE {table}.fid_{key} = {key}.fid) AS {table}"
                            if key == "viheralueenosa" and i != len(TABLE_NAMES) - 2:
                                add_to_query += ", "
                            elif key == "katualueenosa" and i != len(TABLE_NAMES) - 1:
                                add_to_query += ", "
                            else:
                                add_to_query += f" FROM {key[:-5]}.{key}"
                            query +=add_to_query
                else:
                    query = f"SELECT {key}.identifier, (SELECT array_agg({key}enosa.identifier) FROM {key}.{key}enosa WHERE {key}enosa.fid_{key} = {key}.fid) AS {key}enosa FROM {key}.{key}"
                curs.execute(query)
                results = curs.fetchall()
                results_dict = []
                for row in results:
                    results_dict.append(dict(row))
                for row in results_dict:
                    for k in row.keys():
                        if row[k] != None and k != 'identifier':
                            row[k] = row[k][1:-1].split(",")
                results_dicts[key] = results_dict
    return results_dicts


def get_table_values(schema, table, dict_tags, conn_params):
    location_tag = ''
    if table == 'erikoisrakennekerros':
        location_tag = 'SIJAINTI'
    elif table in ['puu','muukasvi']:
        location_tag = 'SIJAINTITIETO'
    elif table not in ['viheralue', 'katualue', 'viheralueenosa', 'katualueenosa', 'keskilinja']:
        location_tag = 'TARKKASIJAINTITIETO'
    else:
        location_tag = None

    columns =  []
    for k, v in dict_tags.items():
        if v[1].startswith("sisaltaa"):
            columns.append((SQL("0"), Identifier(k)))
        elif v[1].startswith("geom") or v[0] in ["infrao:tarkkaSijaintitieto", "infrao:sijainti", "infrao:sijaintitieto"]:
            columns.append((SQL("ST_AsGML({})").format(Identifier(v[1])), Identifier(k)))
        else:
            columns.append((Identifier(v[1]), Identifier(k)))
    values = []
    with(psycopg2.connect(**conn_params)) as conn:
        conn.autocommit = True
        with conn.cursor() as curs:
            select_columns = SQL(',').join(SQL("{} AS {}").format(col, alias) for col, alias in columns)
            query = SQL("SELECT {} from {}.{};").format(select_columns, Identifier(schema), Identifier(table))
            curs.execute(query)
            results = curs.fetchall()
            field_names = [field[0].upper() for field in curs.description]
            for row in results:
                feature_values = {}
                for i, name in enumerate(field_names):
                    feature_values[name] = row[i]
                if location_tag:
                    for n in [location_tag, 'GEOM_LINE', 'GEOM_POINT']:
                        if feature_values[n] == None:
                            del feature_values[n]
                        elif n == location_tag:
                            pass
                        else:
                            feature_values[location_tag] = feature_values[n]
                            del feature_values[n] 
                values.append(feature_values)
    return values


def add_elements(schema, table, dict_tags, gml_fm, result_dicts, conn_params):
    for n, o in globals().items():
        if o is dict_tags:
            dict_name = n
            break
    base_element_name = dict_name[:-5]
    base_element = globals()[base_element_name]

    values = get_table_values(schema, table, dict_tags, conn_params)
    for i in range(len(values)):
        belonging_checked = False
        gml_id = {GML_ID:f"{base_element.removeprefix('infrao:')}.{values[i]['YKSILOINTITIETO']}"}
        f = ET.SubElement(gml_fm, base_element, attrib=gml_id)
        if base_element not in [INFRAO_KESKILINJA, INFRAO_VIHERALUE, INFRAO_KATUALUE]:
            for idx in INFRAO_DIFF_SIJAINTI_TAGS.keys():
                if INFRAO_DIFF_SIJAINTI_TAGS[idx] in values[i].keys():
                    c_sij_parent = ET.SubElement(f, idx)
                    c_sij = ET.SubElement(c_sij_parent, "infrao:Sijainti")
        for key in values[i]:
            xml_tag = dict_tags[key][0]
            if values[i][key] != NULL:#TODO: add missing elements
                if xml_tag in ["infrao:tarkkaSijaintitieto", "infrao:sijainti", "infrao:sijaintitieto"]:
                    if base_element == INFRAO_KESKILINJA:
                        c_base = ET.SubElement(f, xml_tag)
                        gml_string = values[i][key]
                        ns = ' xmlns:gml="http://www.opengis.net/gml/3.2"'
                        ET.register_namespace("gml", "http://www.opengis.net/gml/3.2")
                        p = gml_string.find('srs') -1
                        gml_string = gml_string[:p] + ns + gml_string[p:]
                        c_gml_geom = ET.fromstring(gml_string)
                        c_base.append(c_gml_geom)
                    else:
                        gml_string = values[i][key]
                        ns = ' xmlns:gml="http://www.opengis.net/gml/3.2"'
                        ET.register_namespace("gml", "http://www.opengis.net/gml/3.2")
                        p = gml_string.find('srs') - 1
                        gml_string = gml_string[:p] + ns + gml_string[p:]
                        tags = {"Point": "infrao:piste", "LineString": "infrao:viiva", "Polygon": "infrao:alue"}
                        for gml_geom, io_geom in tags.items():
                            if gml_geom in gml_string:
                                c_io_geom = ET.SubElement(c_sij, io_geom)
                        c_gml_geom = ET.fromstring(gml_string)
                        c_io_geom.append(c_gml_geom)
                elif xml_tag in ["infrao:sijaintiepavarmuus", "infrao:luontitapa"]:
                    c_sij_c = ET.SubElement(c_sij, xml_tag)
                    c_sij_c.text = str(values[i][key])
                elif xml_tag in AREA_NAMES.values() and belonging_checked == 0:
                    belonging_checked = True
                    for key, value in AREA_NAMES.items():
                        find_dict = next((d for d in result_dicts[key] if any(lst and values[i]["YKSILOINTITIETO"] in lst for lst in d.values())), None)
                        if find_dict:
                            if find_dict['identifier'] != values[i]["YKSILOINTITIETO"]:
                                attribs = {
                                "xlink:type": "simple",
                                "xlink:href": f"#{key.capitalize()}.{find_dict['identifier']}"
                                }
                                ET.SubElement(f, value, attribs)
                elif any(xml_tag in i for i in AREA_INCLUDED_NAMES.values()):
                    for key, value in AREA_NAMES.items():
                        find_dict = next((dict_item for dict_item in result_dicts[key] if dict_item.get('identifier') == values[i]['YKSILOINTITIETO']), None)
                        if find_dict is not None:
                            for k, v in find_dict.items():
                                if v == None or k == "identifier":
                                    pass
                                else:
                                    for fi in find_dict[k]:
                                        attribs = {
                                            "xlink:type": "simple",
                                            "xlink:href": f"#{ELEMENT_NAMES[k]}.{fi}"
                                        }
                                        if "Kasvillisuus" in xml_tag:
                                            if k in ["puu", "muukasvi"]:
                                                ET.SubElement(f, xml_tag, attribs)
                                        elif "linja" in xml_tag:
                                            if k == "keskilinja":
                                                ET.SubElement(f, xml_tag, attribs)
                                        else:
                                            if k not in ["puu", "muukasvi", "keskilinja"]:
                                                ET.SubElement(f, xml_tag, attribs)
                elif xml_tag.startswith("infrao:sisaltaa"):
                    pass
                elif xml_tag == "":
                    pass
                elif xml_tag == "infrao:alkuHetki" or xml_tag == "infrao:loppuHetki": #TODO: time zone
                    c_base = ET.SubElement(f, xml_tag)
                    date_time = values[i][key]
                    xsdt_str = date_time.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
                    c_base.text = xsdt_str
                else:
                    c_base = ET.SubElement(f, xml_tag)
                    c_base.text = str(values[i][key])


def xml_export(conn_params, save_file):
    start = time.time()
    LOGGER.info("========================================XML EXPORT STARTED========================================")

    NAMESPACES = {
        "xsi:SchemaLocation": 'www.infra-o.fi http://paikkatietopalvelu.fi/gml/infrao/2.0.2/infrao.xsd',
        "xmlns:xsi":"http://www.w3.org/2001/XMLSchema-instance",
        "xmlns:infrao": 'www.infra-o.fi/infrao',
        "xmlns:xlink":"http://www.w3.org/1999/xlink"
        }
    result_dicts = get_area_identifiers(conn_params)
    LOGGER.info
    root = ET.Element('infrao:InfraoKohteet',  NAMESPACES)
    gml_fm = ET.SubElement(root, GML_FEATURE_MEMBERS)

    for key, value in SCHEMA_TABLE_NAMES.items():
        add_elements(key[0], key[1], value, gml_fm, result_dicts, conn_params)
    tree = ET.ElementTree(root)
    ET.indent(tree, space="\t", level=0)
    tree.write(save_file, xml_declaration=True, encoding="utf-8")
    
    end = time.time()
    LOGGER.info("========================================XML EXPORT ENDED========================================")
    LOGGER.info(f"TIME ELAPSED: {round(((end-start) * 10**3)/1000, 2)} seconds.")


class ExportDialog(QDialog, FORM_CLASS):
    def __init__(self, iface, parent=None):
        QDialog.__init__(self, parent)
        self.setupUi(self)
        self.iface = iface
        self.is_running = False
        
        DLG.populate_dbComboBox(self)

        self.closeButton.clicked.connect(self.close)
        self.filePathButton.clicked.connect(self.get_file_path)
        self.exportButton.clicked.connect(self.execute)

    
    def get_file_path(self):
        save_file, _ = QFileDialog.getSaveFileName(None, "Save File", "", "GML Files (*.gml)")
        if save_file:
            if not save_file.endswith('.gml'):
                save_file += '.gml'
        self.filePathLineEdit.setText(save_file)

    
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
        save_file = self.filePathLineEdit.value()
        try:
            xml_export(conn_params, save_file)
            iface.messageBar().pushMessage(f"Tiedosto tallennettu polkuun: {save_file}", level=3, duration=10)
        except FileNotFoundError:
            iface.messageBar().pushMessage("Virheellinen tiedostopolku. Tiedostoa ei voitu tallentaa", level=1, duration=5)
        except PermissionError:
            iface.messageBar().pushMessage("Pääsy estetty hakemistoon. Tarkista tallennuspolku.", level=1, duration=5)