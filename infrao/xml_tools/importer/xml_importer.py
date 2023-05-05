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

from ...qgis_plugin_tools.tools.resources import plugin_name, load_ui
from qgis.core import NULL
from qgis.utils import iface
from osgeo import ogr
from osgeo.osr import CoordinateTransformation

from lxml import etree

import psycopg2
from psycopg2.sql import SQL, Placeholder, Identifier

from ...ui.init_db import Dialog as DLG
from ...db.db_utils import get_db_connection_params
from ...ui.ask_credentials import DbAskCredentialsDialog

from PyQt5.QtWidgets import QDialog, QFileDialog

import time



CORE_NS_LONG = "{www.infra-o.fi/infrao}"
GML_NS_LONG = "{http://www.opengis.net/gml/3.2}"
XLINK_NS_LONG = "{http://www.w3.org/1999/xlink}"



# infrao abstractpaikkatietopalvelukohde tags
INFRAO_ABSTRACT_PAIKKATIETOPALVELUKOHDE = {
    CORE_NS_LONG + "metatieto": "metatieto",
    CORE_NS_LONG + "yksilointitieto": "identifier",
    CORE_NS_LONG + "alkuHetki": "alkuhetki",
    CORE_NS_LONG + "loppuHetki": "loppuhetki",
}

# infrao abstractvaruste tags
INFRAO_ABSTRACT_VARUSTE = {#TODO: suunnitelmalinkkitieto, geometry
    CORE_NS_LONG + "omistaja": "omistaja",
    CORE_NS_LONG + "haltija": "haltija",
    CORE_NS_LONG + "kunnossapitaja": "kunnossapitaja",
    CORE_NS_LONG + "malli": "malli",
    CORE_NS_LONG + "perusparannusvuosi": "perusparannusvuosi",
    CORE_NS_LONG + "suunta": "suunta",
    CORE_NS_LONG + "valmistaja": "valmistaja",
    CORE_NS_LONG + "valmistumisvuosi": "valmistumisvuosi",
    CORE_NS_LONG + "materiaali": "cid_varustemateriaali",
    CORE_NS_LONG + "kuuluuViheralueenOsaan": "fid_viheralueenosa",
    CORE_NS_LONG + "kuuluuKatuAlueenOsaan": "fid_katualueenosa",
    CORE_NS_LONG + "sijaintiepavarmuus": "cid_sijaintiepavarmuustyyppi",
    CORE_NS_LONG + "luontitapa": "cid_luontitapatyyppi",
    CORE_NS_LONG + "alue": "geom_poly",
    CORE_NS_LONG + "piste": "geom_point",
    CORE_NS_LONG + "viiva": "geom_line",
}

# infrao abstractkasvillisuus tags
INFRAO_ABSTRACT_KASVILLISUUS = {
    CORE_NS_LONG + "omistaja": "omistaja",
    CORE_NS_LONG + "haltija": "haltija",
    CORE_NS_LONG + "kunnossapitaja": "kunnossapitaja",
    CORE_NS_LONG + "kuuluuViheralueenOsaan": "fid_viheralueenosa",
    CORE_NS_LONG + "kuuluuKatuAlueenOsaan": "fid_katualueenosa",
    CORE_NS_LONG + "sijaintiepavarmuus": "cid_sijaintiepavarmuustyyppi",
    CORE_NS_LONG + "luontitapa": "cid_luontitapatyyppi",
    CORE_NS_LONG + "alue": "geom_poly",
    CORE_NS_LONG + "piste": "geom_point",
    CORE_NS_LONG + "viiva": "geom_line",
}

## ELEMENT TAGS
# infrao:Ajoratamerkinta unique tags -> inherit abstractpaikkatietopalvelukohde and abstractvaruste
INFRAO_AJORATAMERKINTA_TAGS = {
    CORE_NS_LONG + "jyrsittyPintaKytkin": "jyrsittypinta_kytkin",
    CORE_NS_LONG + "tyyppi": "cid_ajoratamerkintatyyppi"
}
INFRAO_AJORATAMERKINTA_TAGS |= INFRAO_ABSTRACT_PAIKKATIETOPALVELUKOHDE
INFRAO_AJORATAMERKINTA_TAGS |= INFRAO_ABSTRACT_VARUSTE

# infrao:ErikoisrakenneKerros -> inherit abstractpaikkatietopalvelukohde
INFRAO_ERIKOISRAKENNEKERROS_TAGS = {}
INFRAO_ERIKOISRAKENNEKERROS_TAGS |= INFRAO_ABSTRACT_PAIKKATIETOPALVELUKOHDE

INFRAO_ERIKOISRAKENNEKERROS_TAGS = {
    CORE_NS_LONG + "omistaja": "omistaja",
    CORE_NS_LONG + "haltija": "haltija",
    CORE_NS_LONG + "kunnossapitaja": "kunnossapitaja",
    CORE_NS_LONG + "selite": "selite",
    CORE_NS_LONG + "materiaali": "materiaali",
    CORE_NS_LONG + "tyyppi": "cid_erikoisrakennekerrosmateriaalityyppi",
    CORE_NS_LONG + "sijaintiepavarmuus": "cid_sijaintiepavarmuustyyppi",
    CORE_NS_LONG + "luontitapa": "cid_luontitapatyyppi",
    CORE_NS_LONG + "alue": "geom_poly",
    CORE_NS_LONG + "piste": "geom_point",
    CORE_NS_LONG + "viiva": "geom_line",
}


# infrao:Hulevesi unique tags -> inherit abstractpaikkatietopalvelukohde and abstractvaruste
INFRAO_HULEVESI_TAGS = {
    CORE_NS_LONG + "hulevesi": "cid_hulevesityyppi"
}
INFRAO_HULEVESI_TAGS |= INFRAO_ABSTRACT_PAIKKATIETOPALVELUKOHDE
INFRAO_HULEVESI_TAGS |= INFRAO_ABSTRACT_VARUSTE

# infrao:Jate unique tags -> inherit abstractpaikkatietopalvelukohde and abstractvaruste
INFRAO_JATE_TAGS = {
    CORE_NS_LONG + "koko": "koko",
    CORE_NS_LONG + "putkikeraysjarjestelmaKytkin": "putkikeraysjarjestelma_kytkin",
    CORE_NS_LONG + "sijaintiMaanPinnallaKytkin": "sijaintimaanpinnalla_kytkin",
    CORE_NS_LONG + "vaarallistenJateastiaKytkin": "vaarallistenjateastia_kytkin",
    CORE_NS_LONG + "jate": "cid_jatetyyppi"
}
INFRAO_JATE_TAGS |= INFRAO_ABSTRACT_PAIKKATIETOPALVELUKOHDE
INFRAO_JATE_TAGS |= INFRAO_ABSTRACT_VARUSTE

# infrao:Kaluste unique tags -> inherit abstractpaikkatietopalvelukohde and abstractvaruste
INFRAO_KALUSTE_TAGS = {
    CORE_NS_LONG + "kaluste": "cid_kalustetyyppi"
}
INFRAO_KALUSTE_TAGS |= INFRAO_ABSTRACT_PAIKKATIETOPALVELUKOHDE
INFRAO_KALUSTE_TAGS |= INFRAO_ABSTRACT_VARUSTE

# infrao:Katualue unique tags -> inherit abstractpaikkatietopalvelukohde
INFRAO_KATUALUE_TAGS = {
    #CORE_NS_LONG + "sisaltaaKatualueenOsan": "sisaltaakatualueenosan",
    CORE_NS_LONG + "nimi": "nimi"
}
INFRAO_KATUALUE_TAGS |= INFRAO_ABSTRACT_PAIKKATIETOPALVELUKOHDE

# infrao:KatualueenOsa unique tags -> inherit abstractpaikkatietopalvelukohde
INFRAO_KATUALUEENOSA_TAGS = {}
INFRAO_KATUALUEENOSA_TAGS |= INFRAO_ABSTRACT_PAIKKATIETOPALVELUKOHDE

INFRAO_KATUALUEENOSA_TAGS |= {
    #"PAATOSTIETO": [CORE_NS + ":paatostieto": TODO: add later
    CORE_NS_LONG + "omistaja": "omistaja",
    CORE_NS_LONG + "haltija": "haltija",
    CORE_NS_LONG + "kunnossapitaja": "kunnossapitaja",
    CORE_NS_LONG + "kunnossapito": "kunnossapito",
    CORE_NS_LONG + "leveys": "leveys",
    CORE_NS_LONG + "perusparannusvuosi": "perusparannusvuosi",
    CORE_NS_LONG + "pintaAla": "pinta_ala",
    CORE_NS_LONG + "pituus": "pituus",
    CORE_NS_LONG + "puhtaanapito": "puhtaanapito",
    CORE_NS_LONG + "talvikunnossapito": "talvikunnossapito",
    CORE_NS_LONG + "valmistumisvuosi": "valmistumisvuosi",
    CORE_NS_LONG + "kuuluuKatualueeseen": "fid_katualue",
    #CORE_NS_LONG + "sisaltaaKeskilinja": "sisaltaakeskilinja", TODO: HANDLE THESE
    CORE_NS_LONG + "luokka": "luokka_id",
    CORE_NS_LONG + "laji": "katuosanlaji_id",
    CORE_NS_LONG + "viheralueenLaji": "viherosanlajityyppi_id",
    CORE_NS_LONG + "pintamateriaali": "pintamateriaali_id",
    CORE_NS_LONG + "kunnossapitoluokka": "kunnossapitoluokka_id",
    #"SUUNNITELMALINKKITIETO": [CORE_NS + ":suunnitelmalinkkitieto": "": #TODO: add later
    CORE_NS_LONG + "talvihoidonLuokka": "talvihoidonluokka_id",
    #CORE_NS_LONG + "sisaltaaKasvillisuus": "sisaltaakasvillisuus",
    #CORE_NS_LONG + "sisaltaaVaruste": "sisaltaavaruste",
    CORE_NS_LONG + "sijaintiepavarmuus": "cid_sijaintiepavarmuustyyppi",
    CORE_NS_LONG + "luontitapa": "cid_luontitapatyyppi",
    CORE_NS_LONG + "alue": "geom",
}


# infrao:Keskilinja unique tags -> inherit abstractpaikkatietopalvelukohde
INFRAO_KESKILINJA_TAGS = {}
INFRAO_KESKILINJA_TAGS |= INFRAO_ABSTRACT_PAIKKATIETOPALVELUKOHDE

INFRAO_KESKILINJA_TAGS |= {
    CORE_NS_LONG + "DigiroadID": "digiroadid",
    CORE_NS_LONG + "kuuluuKatualueenOsaan": "fid_katualueenosa",
    CORE_NS_LONG + "sijainti": "geom",
}


# infrao:Leikkivaline unique tags -> inherit abstractpaikkatietopalvelukohde and abstractvaruste
INFRAO_LEIKKIVALINE_TAGS = {
    CORE_NS_LONG + "toiminnallinenTarkastusPvm": "toiminnallinentarkastus_pvm",
    CORE_NS_LONG + "vuositarkastusPvm": "vuositarkastus_pvm",
    CORE_NS_LONG + "leikkivaline": "cid_leikkivalinetyyppi"
}
INFRAO_LEIKKIVALINE_TAGS |= INFRAO_ABSTRACT_PAIKKATIETOPALVELUKOHDE
INFRAO_LEIKKIVALINE_TAGS |= INFRAO_ABSTRACT_VARUSTE

# infrao:Liikennemerkki tags -> inherit abstractpaikkatietopalvelukohde and abstractvaruste
INFRAO_LIIKENNEMERKKI_TAGS = {
    CORE_NS_LONG + "teksti": "teksti",
    CORE_NS_LONG + "liikennemerkkityyppi": "cid_liikennemerkkityyppi",
    CORE_NS_LONG + "liikennemerkkityyppi2020": "cid_liikennemerkkityyppi2020",
}
INFRAO_LIIKENNEMERKKI_TAGS |= INFRAO_ABSTRACT_PAIKKATIETOPALVELUKOHDE
INFRAO_LIIKENNEMERKKI_TAGS |= INFRAO_ABSTRACT_VARUSTE

# infrao:Liikunta unique tags > inherit abstractpaikkatietopalvelukohde and abstractvaruste
INFRAO_LIIKUNTA_TAGS = {
    CORE_NS_LONG + "liikunta": "cid_liikuntatyyppi"
}
INFRAO_LIIKUNTA_TAGS |= INFRAO_ABSTRACT_PAIKKATIETOPALVELUKOHDE
INFRAO_LIIKUNTA_TAGS |= INFRAO_ABSTRACT_VARUSTE

# infrao:Liite unique tags
INFRAO_LIITE_TAGS = {#TODO: remove if not needed
    CORE_NS_LONG + "kuvaus": "kuvaus",
    CORE_NS_LONG + "linkkiliitteeseen": "linkkiliitteeseen",
    CORE_NS_LONG + "muokkausHetki": "muokkaushetki",
    CORE_NS_LONG + "versionumero": "versionumero"
}

# infrao:Melu unique tags -> inherit abstractpaikkatietopalvelukohde and abstractvaruste
INFRAO_MELU_TAGS = {
    CORE_NS_LONG + "melu": "cid_melutyyppi"
}
INFRAO_MELU_TAGS |= INFRAO_ABSTRACT_PAIKKATIETOPALVELUKOHDE
INFRAO_MELU_TAGS |= INFRAO_ABSTRACT_VARUSTE

# infrao:MuuKasvi unique tags -> inherit abstractpaikkatietopalvelukohde and abstractkasvillisuus
INFRAO_MUUKASVI_TAGS = {
    CORE_NS_LONG + "kasviryhma": "cid_kasviryhmatyyppi",
    CORE_NS_LONG + "kasvilaji": "cid_kasvilaji"

}
INFRAO_MUUKASVI_TAGS |= INFRAO_ABSTRACT_PAIKKATIETOPALVELUKOHDE
INFRAO_MUUKASVI_TAGS |= INFRAO_ABSTRACT_KASVILLISUUS

# infrao:MuuVaruste unique tags -> inherit abstractpaikkatietopalvelukohde and abstractvaruste
INFRAO_MUUVARUSTE_TAGS = {
    CORE_NS_LONG + "varustetyyppi": "cid_muuvarustetyyppi"
}
INFRAO_MUUVARUSTE_TAGS |= INFRAO_ABSTRACT_PAIKKATIETOPALVELUKOHDE
INFRAO_MUUVARUSTE_TAGS |= INFRAO_ABSTRACT_VARUSTE

# infrao:Opaste unique tags -> inherit abstractpaikkatietopalvelukohde and abstractvaruste
INFRAO_OPASTE_TAGS = {
    CORE_NS_LONG + "opaste": "cid_opastetyyppi"
}
INFRAO_OPASTE_TAGS |= INFRAO_ABSTRACT_PAIKKATIETOPALVELUKOHDE
INFRAO_OPASTE_TAGS |= INFRAO_ABSTRACT_VARUSTE

# infrao:Puu unique tags -> inherit abstractpaikkatietopalvelukohde and abstractkasvillisuus
INFRAO_PUU_TAGS = {
    CORE_NS_LONG + "korkeusMitta": "korkeus",
    CORE_NS_LONG + "ymparysMitta": "ymparys",
    CORE_NS_LONG + "puutyyppi": "cid_puutyyppi",
    CORE_NS_LONG + "puulaji": "cid_puulaji"
}
INFRAO_PUU_TAGS |= INFRAO_ABSTRACT_PAIKKATIETOPALVELUKOHDE
INFRAO_PUU_TAGS |= INFRAO_ABSTRACT_KASVILLISUUS

# infrao:Pysakointiruutu unique tags -> inherit abstractpaikkatietopalvelukohde and abstractvaruste
INFRAO_PYSAKOINTIRUUTU_TAGS = {
    CORE_NS_LONG + "latauspisteKytkin": "latauspiste_kytkin"
}
INFRAO_PYSAKOINTIRUUTU_TAGS |= INFRAO_ABSTRACT_PAIKKATIETOPALVELUKOHDE
INFRAO_PYSAKOINTIRUUTU_TAGS |= INFRAO_ABSTRACT_VARUSTE

# infrao:Rakenne unique tags -> inherit abstractpaikkatietopalvelukohde and abstractvaruste
INFRAO_RAKENNE_TAGS = {
    CORE_NS_LONG + "rakenne": "cid_rakennetyyppi"
}
INFRAO_RAKENNE_TAGS |= INFRAO_ABSTRACT_PAIKKATIETOPALVELUKOHDE
INFRAO_RAKENNE_TAGS |= INFRAO_ABSTRACT_VARUSTE

# infrao:Suunnitelmalinkki unique tags
INFRAO_SUUNNITELMALINKKI_TAGS = { #TODO: remove if not needed
    CORE_NS_LONG + "SuunnitelmakohdeId",
    CORE_NS_LONG + "liitetieto"
}

# infrao:Viheralue unique tags -> inherit abstract paikkatietopalvelukohde
INFRAO_VIHERALUE_TAGS = {
    CORE_NS_LONG + "nimi": "nimi",
}
INFRAO_VIHERALUE_TAGS |= INFRAO_ABSTRACT_PAIKKATIETOPALVELUKOHDE

# infrao:ViheralueenOsa unique tags -> inherit abstract paikkatietopalvelukohde
INFRAO_VIHERALUEENOSA_TAGS = {}
INFRAO_VIHERALUEENOSA_TAGS |= INFRAO_ABSTRACT_PAIKKATIETOPALVELUKOHDE
INFRAO_VIHERALUEENOSA_TAGS |= {
    CORE_NS_LONG + "omistaja": "omistaja",
    CORE_NS_LONG + "haltija": "haltija",
    CORE_NS_LONG + "kunnossapitaja": "kunnossapitaja",
    CORE_NS_LONG + "perusparannusvuosi": "perusparannusvuosi",
    CORE_NS_LONG + "valmistumisvuosi": "valmistumisvuosi",
    CORE_NS_LONG + "suojelualuekytkin": "suojelualuekytkin",
    CORE_NS_LONG + "kuuluuViheralueeseen": "fid_viheralue",
    CORE_NS_LONG + "kayttotarkoitus": "kayttotarkoitus_id",
    CORE_NS_LONG + "laji": "laji_id",
    CORE_NS_LONG + "hoitoluokka": "hoitoluokka_id",
    CORE_NS_LONG + "katualueenLaji": "katualueenlaji_id",
    CORE_NS_LONG + "suunnitelmalinkkitieto": "suunnitelmalinkkitieto_id",
    CORE_NS_LONG + "talvihoidonLuokka": "talvihoidonluokka_id",
    CORE_NS_LONG + "puhtaanapitoluokka": "puhtaanapitoluokka_id",
    CORE_NS_LONG + "muutoshoitoluokka": "muutoshoitoluokka_id",
    #CORE_NS_LONG + "sisaltaaKasvillisuus": "sisaltaakasvillisuus",
    #CORE_NS_LONG + "sisaltaaVaruste": "sisaltaavaruste",
    CORE_NS_LONG + "sijaintiepavarmuus": "cid_sijaintiepavarmuustyyppi",
    CORE_NS_LONG + "luontitapa": "cid_luontitapatyyppi",
    CORE_NS_LONG + "alue": "geom",
}

# infrao:Ymparistotaide unique tags -> inherit abstractpaikkatietopalvelukohde and abstractvaruste
INFRAO_YMPARISTOTAIDE_TAGS = {
    CORE_NS_LONG + "ymparistotaide": "cid_ymparistotaidetyyppi"
}
INFRAO_YMPARISTOTAIDE_TAGS |= INFRAO_ABSTRACT_PAIKKATIETOPALVELUKOHDE
INFRAO_YMPARISTOTAIDE_TAGS |= INFRAO_ABSTRACT_VARUSTE

AREA_TABLE_LIST = [
    ("katualue", "katualue"),
    ("viheralue", "viheralue"),
]

AREA_PART_TABLE_LIST = [
    ("viheralue", "viheralueenosa"),
    ("katualue", "katualueenosa"),
]

TABLE_LIST = [
    ("varusteet","jate"),
    ("varusteet","kaluste"),
    ("varusteet","leikkivaline"),
    ("varusteet","liikunta"),
    ("varusteet","melukohde"),
    ("varusteet","muuvaruste"),
    ("varusteet","opaste"),
    ("varusteet", "liikennemerkki"),
    ("kasvillisuus", "puu"),
    ("kasvillisuus", "muukasvi"),
    ("kohteet", "erikoisrakennekerros"),
    ("kohteet", "hulevesi"),
    ("kohteet", "pysakointiruutu"),
    ("kohteet", "rakenne"),
    ("kohteet", "ymparistotaide"),
    ("katualue", "keskilinja"),
    ("katualue", "ajoratamerkinta"),
]

TABLE_TO_ELEMENT = {
    "jate": [CORE_NS_LONG + "Jate", INFRAO_JATE_TAGS],
    "kaluste": [CORE_NS_LONG + "Kaluste", INFRAO_KALUSTE_TAGS],
    "leikkivaline": [CORE_NS_LONG + "Leikkivaline", INFRAO_LEIKKIVALINE_TAGS],
    "liikunta": [CORE_NS_LONG + "Liikunta", INFRAO_LIIKUNTA_TAGS],
    "melukohde": [CORE_NS_LONG + "Melu", INFRAO_MELU_TAGS],
    "muuvaruste": [CORE_NS_LONG + "MuuVaruste", INFRAO_MUUVARUSTE_TAGS],
    "opaste": [CORE_NS_LONG + "Opaste", INFRAO_OPASTE_TAGS],
    "liikennemerkki": [CORE_NS_LONG + "Liikennemerkki", INFRAO_LIIKENNEMERKKI_TAGS],
    "viheralueenosa": [CORE_NS_LONG + "ViheralueenOsa", INFRAO_VIHERALUEENOSA_TAGS],
    "viheralue": [CORE_NS_LONG + "Viheralue", INFRAO_VIHERALUE_TAGS],
    "katualue": [CORE_NS_LONG + "Katualue", INFRAO_KATUALUE_TAGS],
    "katualueenosa": [CORE_NS_LONG + "KatualueenOsa", INFRAO_KATUALUEENOSA_TAGS],
    "keskilinja": [CORE_NS_LONG + "Keskilinja", INFRAO_KESKILINJA_TAGS],
    "ajoratamerkinta": [CORE_NS_LONG + "Ajoratamerkinta", INFRAO_AJORATAMERKINTA_TAGS],
    "puu": [CORE_NS_LONG + "Puu", INFRAO_PUU_TAGS],
    "muukasvi": [CORE_NS_LONG + "MuuKasvi", INFRAO_MUUKASVI_TAGS],
    "erikoisrakennekerros": [CORE_NS_LONG + "ErikoisrakenneKerros", INFRAO_ERIKOISRAKENNEKERROS_TAGS],
    "hulevesi": [CORE_NS_LONG + "Hulevesi", INFRAO_HULEVESI_TAGS],
    "pysakointiruutu": [CORE_NS_LONG + "Pysakointiruutu", INFRAO_PYSAKOINTIRUUTU_TAGS],
    "rakenne": [CORE_NS_LONG + "Rakenne", INFRAO_RAKENNE_TAGS],
    "ymparistotaide": [CORE_NS_LONG + "Ymparistotaide", INFRAO_YMPARISTOTAIDE_TAGS],
}

AREA_TAG_TO_TABLE = {
    CORE_NS_LONG + "kuuluuViheralueeseen": "viheralue",
    CORE_NS_LONG + "kuuluuKatualueeseen": "katualue",
    CORE_NS_LONG + "kuuluuViheralueenOsaan": "viheralueenosa",
    CORE_NS_LONG + "kuuluuKatuAlueenOsaan": "katualueenosa",
}

FORM_CLASS = load_ui('import.ui')
LOGGER = logging.getLogger(plugin_name())

def get_area_fids(conn_params): #TODO: modify the function so that the result is a dictionary where identifier -> fid
    results_dicts = {"viheralueenosa": [],
                     "katualueenosa": [],
                     "viheralue": [],
                     "katualue": [],}
    for key in results_dicts.keys():
        if key.startswith('k'):
            schema = "katualue"
        else:
            schema = "viheralue"

        query = f"SELECT fid, identifier FROM {schema}.{key};" # TODO: use psycopg2.sql

        with(psycopg2.connect(**conn_params)) as conn:
            with conn.cursor() as curs:
                curs.execute(query)
                rows = curs.fetchall()
                result_dict = {}
                for row in rows:
                    result_dict[row[1]] = row[0]
                results_dicts[key] = result_dict
    return results_dicts

def get_values_from_xml(table, file_path, results_dicts): # TODO: handle timestamps
    element = TABLE_TO_ELEMENT[table][0]
    element_dict = TABLE_TO_ELEMENT[table][1]

    tree = etree.parse(file_path)
    root = tree.getroot()

    values_dict = []
    for feature in root.iter(element):
        value_dict = {key: None for key in element_dict.values()}
        for child in feature.iter():
            if child.tag in element_dict.keys():
                if not child.tag in [CORE_NS_LONG + "kuuluuKatualueeseen", CORE_NS_LONG + "kuuluuViheralueeseen", CORE_NS_LONG + "kuuluuKatuAlueenOsaan", CORE_NS_LONG + "kuuluuViheralueenOsaan", CORE_NS_LONG + "tarkkaSijaintitieto", CORE_NS_LONG + "sijaintitieto", CORE_NS_LONG + "sijainti", CORE_NS_LONG + "Sijainti", CORE_NS_LONG + "piste", CORE_NS_LONG + "viiva", CORE_NS_LONG + "alue", CORE_NS_LONG + "alkuHetki", CORE_NS_LONG + "loppuHetki",] and not child.tag.startswith(GML_NS_LONG):
                    value_dict[element_dict[child.tag]] = child.text
                elif child.tag in [CORE_NS_LONG + "alue", CORE_NS_LONG + "viiva", CORE_NS_LONG + "piste"] or table == 'keskilinja' and child.tag == CORE_NS_LONG + "sijainti": #TODO: check SRS
                    gml_elem = child.find('*')
                    gml_string = etree.tostring(gml_elem).decode('utf-8')
                    geom = ogr.CreateGeometryFromGML(gml_string)
                    if geom:
                        value_dict[element_dict[child.tag]] = geom.ExportToWkb()
                elif child.tag.startswith(CORE_NS_LONG + "kuuluu"):
                    try:
                        belong_attrib = child.attrib[XLINK_NS_LONG + "href"]
                        dot_pos = belong_attrib.find('.')
                        if dot_pos != -1:
                            id = belong_attrib[dot_pos + 1:]
                            try:
                                value_dict[element_dict[child.tag]] = results_dicts[AREA_TAG_TO_TABLE[child.tag]][id]
                            except:
                                LOGGER.info(f"Kohteen {feature.tag} sisältävän alueen yksilöintitietoa ei löytynyt.")
                    except KeyError:
                        LOGGER.info(f"Kohteen {feature.tag} elementti {child.tag} ei sisällä xlink- attribuuttia.")
        values_dict.append(value_dict)
    return values_dict


def build_sql_query(values_dict, schema, table):
    table_name = Identifier(schema, table)

    keys = list(values_dict[0].keys())
    values = [value for dict in values_dict for value in dict.values()]

    values_template = SQL(", ").join(
        Placeholder() if i < len(keys) - 3 or table in ['katualue', 'viheralue'] or i < len(keys) - 1 and table in ['katualueenosa', 'viheralueenosa', 'keskilinja'] else SQL("ST_Force3D(ST_GeomFromEWKB({}))").format(Placeholder())
        for i in range(len(keys))
    )  

    query = SQL("INSERT INTO {} ({}) VALUES {}").format(
        table_name,
        SQL(',').join(map(Identifier, keys)),
        SQL(", ").join(SQL("({})").format(values_template) * len(values_dict))
    )
    return query, values


def add_features_to_database(query, values, conn_params):
    with(psycopg2.connect(**conn_params)) as conn:
        with conn.cursor() as curs:
            #LOGGER.info(query.as_string(curs)) #TODO: remove
            #LOGGER.info(values)
            curs.execute(query, values)


def xml_import(conn_params, file_path):
    start = time.time()
    LOGGER.info("========================================XML IMPORT STARTED========================================")
    
    for schema, table in AREA_TABLE_LIST:
        values_dict = get_values_from_xml(table, file_path, None)
        if not values_dict == []:
            LOGGER.info(f"Yritetään lisätä kohteita tauluun: {table}")
            query, values = build_sql_query(values_dict, schema, table)
            add_features_to_database(query, values, conn_params)
            LOGGER.info(f"Kohteet lisätty tauluun: {table}")
    results_dicts = get_area_fids(conn_params)

    for schema, table in AREA_PART_TABLE_LIST:
        values_dict = get_values_from_xml(table, file_path, results_dicts)
        if not values_dict == []:
            LOGGER.info(f"Yritetään lisätä kohteita tauluun: {table}")
            query, values = build_sql_query(values_dict, schema, table)
            add_features_to_database(query, values, conn_params)
            LOGGER.info(f"Kohteet lisätty tauluun: {table}")
    results_dicts = get_area_fids(conn_params)

    for schema, table in TABLE_LIST:
        values_dict = get_values_from_xml(table, file_path, results_dicts)
        if not values_dict == []:
            LOGGER.info(f"Yritetään lisätä kohteita tauluun: {table}")
            query, values = build_sql_query(values_dict, schema, table)
            add_features_to_database(query, values, conn_params)
            LOGGER.info(f"Kohteet lisätty tauluun: {table}")

    canvas = iface.mapCanvas()
    canvas.refreshAllLayers()

    end = time.time()
    LOGGER.info("========================================XML IMPORT ENDED  ========================================")
    LOGGER.info(f"TIME ELAPSED: {round(((end-start) * 10**3)/1000, 2)} seconds.")
    iface.messageBar().pushMessage(f"Kohteet tiedostosta {file_path} tuotu onnistuneesti tietokantaan.", level=3, duration=10)


class ImportDialog(QDialog, FORM_CLASS):
    def __init__(self, iface, parent=None):
        QDialog.__init__(self, parent)
        self.setupUi(self)
        self.iface = iface
        self.is_running = False
        
        DLG.populate_dbComboBox(self)

        self.closeButton.clicked.connect(self.close)
        self.filePathButton.clicked.connect(self.get_file_path)
        self.importButton.clicked.connect(self.execute)

    
    def get_file_path(self):
        open_file, _ = QFileDialog.getOpenFileName(None, "Open File", "", "GML Files (*.gml)")
        if open_file:
            if not open_file.endswith('.gml'):
                open_file += '.gml'
        self.filePathLineEdit.setText(open_file)

    
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
        open_file = self.filePathLineEdit.value()
        try:
            xml_import(conn_params, open_file)
        except FileNotFoundError:
            iface.messageBar().pushMessage("Virheellinen tiedostopolku. Tietoja ei voitu tuoda.", level=1, duration=5)
        except PermissionError:
            iface.messageBar().pushMessage("Pääsy estetty hakemistoon. Tarkista tiedoston polku.", level=1, duration=5)