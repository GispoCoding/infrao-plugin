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
from ...qgis_plugin_tools.tools.resources import plugin_name
from lxml import etree

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


)

conn_params = {'dbname': 'infrao', 'host': 'localhost', 'password': 'mysecretpassu', 'port': '5434', 'user': 'infrao_admin'}

LOGGER = logging.getLogger(plugin_name())

def xml_import():
    tree = etree.parse('C:/Users/juho-/Desktop/output.gml')
    root = tree.getroot()
    for feature in root.iter():
        LOGGER.info(feature)
    LOGGER.info("XML imported")