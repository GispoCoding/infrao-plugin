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
from qgis.core import QgsCoordinateTransform, QgsProject, QgsGeometry
from qgis.utils import iface
from osgeo import ogr

from xml.etree import ElementTree as ET

import psycopg2
from psycopg2.sql import SQL, Placeholder, Identifier, Composed
from psycopg2.extras import DictCursor

import time



CORE_NS_LONG = "{www.infra-o.fi/infrao}"
GML_NS_LONG = "{http://www.opengis.net/gml/3.2}"
GML_NS_LONG_DICT = {"gml": "http://www.opengis.net/gml/3.2"}
XLINK_NS_LONG = "{http://www.w3.org/1999/xlink}"
SYSTEM_EPSG = 3067
SIJAINTI_TAGS = [CORE_NS_LONG + "tarkkaSijaintitieto", CORE_NS_LONG + "sijaintitieto", CORE_NS_LONG + "sijainti"]
INFRAO_GEOMS = [CORE_NS_LONG + "piste", CORE_NS_LONG + "alue", CORE_NS_LONG + "viiva",]



# infrao abstractpaikkatietopalvelukohde tags
INFRAO_ABSTRACT_PAIKKATIETOPALVELUKOHDE = {
    CORE_NS_LONG + "metatieto": "skip",
    CORE_NS_LONG + "osoitetieto": "skip",
    "datan_luoja": "meta_datanluoja",
    "muokkaaja": "meta_muokkaaja",
    "muokkaus_pvm": "meta_muokkauspvm",
    "omistaja": "meta_omistaja",
    "lahteen_pvm": "meta_lahteenpvm",
    "mittausera": "meta_mittausera",
    "lisatieto_linkki": "meta_lisatietolinkki",
    CORE_NS_LONG + "yksilointitieto": "identifier",
    CORE_NS_LONG + "alkuHetki": "alkuhetki",
    CORE_NS_LONG + "loppuHetki": "loppuhetki",}

# infrao abstractvaruste tags
INFRAO_ABSTRACT_VARUSTE = {
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
    CORE_NS_LONG + "suunnitelmalinkkitieto": "skip",
    "skip": "fid_osoite",
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
    "skip": "fid_osoite",
    CORE_NS_LONG + "alue": "geom_poly",
    CORE_NS_LONG + "piste": "geom_point",
    CORE_NS_LONG + "viiva": "geom_line",
}


INFRAO_AINEISTOTOIMITUKSEN_TIEDOT = {
    CORE_NS_LONG + "aineistonnimi": "aineistonnimi",
    CORE_NS_LONG + "aineistotoimittaja": "aineistotoimittaja",
    CORE_NS_LONG + "tila": "tila",
    CORE_NS_LONG + "toimitusPvm": "toimituspvm",
    CORE_NS_LONG + "kuntakoodi": "kuntakoodi",
    CORE_NS_LONG + "kielitieto": "kielitieto",
    CORE_NS_LONG + "metatietotunniste": "metatietotunniste",
    CORE_NS_LONG + "metatietoXMLURL": "metatietoxmlurl",
    CORE_NS_LONG + "metatietoURL": "metatietourl",
    CORE_NS_LONG + "tietotuoteURL": "tietotuoteurl",
}

# infrao:Osoite unique tags
INFRAO_OSOITE_TAGS = {
    CORE_NS_LONG + "kunta": "kunta",
    CORE_NS_LONG + "osoitenumero": "osoitenumero",
    CORE_NS_LONG + "osoitenumero2": "osoitenumero2",
    CORE_NS_LONG + "jakokirjain": "jakokirjain",
    CORE_NS_LONG + "jakokirjain2": "jakokirjain2",
    CORE_NS_LONG + "porras": "porras",
    CORE_NS_LONG + "huoneisto": "huoneisto",
    CORE_NS_LONG + "huoneistojakokirjain": "huoneistojakokirjain",
    CORE_NS_LONG + "postinumero": "postinumero",
    CORE_NS_LONG + "postitoimipaikannimi": "postitoimipaikannimi",
    CORE_NS_LONG + "pistesijainti": "geom_point",
    CORE_NS_LONG + "aluesijainti": "geom_poly",
    CORE_NS_LONG + "viivasijainti": "geom_line",
    CORE_NS_LONG + "viitesijaintialue": "viitesijaintialue",
    CORE_NS_LONG + "nimitieto": "nimitieto",
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
    CORE_NS_LONG + "selite": "erk_selite",
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
    CORE_NS_LONG + "luokka": "cid_toiminnallinenluokka",
    CORE_NS_LONG + "laji": "cid_katuosanlaji",
    CORE_NS_LONG + "viheralueenLaji": "cid_viherosanlajityyppi",
    CORE_NS_LONG + "pintamateriaali": "cid_pintamateriaali",
    CORE_NS_LONG + "kunnossapitoluokka": "cid_hoitoluokkatyyppi",
    CORE_NS_LONG + "talvihoidonLuokka": "cid_talvihoidonluokka",
    CORE_NS_LONG + "sijaintiepavarmuus": "cid_sijaintiepavarmuustyyppi",
    CORE_NS_LONG + "luontitapa": "cid_luontitapatyyppi",
    "skip": "fid_osoite",
    CORE_NS_LONG + "suunnitelmalinkkitieto": "skip",
    CORE_NS_LONG + "paatostieto": "skip",
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
INFRAO_LIITE_TAGS = {
    CORE_NS_LONG + "kuvaus": "kuvaus",
    CORE_NS_LONG + "linkkiliitteeseen": "linkkiliitteeseen",
    CORE_NS_LONG + "muokkausHetki": "muokkaushetki",
    CORE_NS_LONG + "versionumero": "versionumero",
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
    CORE_NS_LONG + "kayttotarkoitus": "cid_viheralueenkayttotarkoitus",
    CORE_NS_LONG + "laji": "cid_viherosanlajityyppi",
    CORE_NS_LONG + "hoitoluokka": "cid_hoitoluokkatyyppi",
    CORE_NS_LONG + "katualueenLaji": "cid_katuosanlaji",
    CORE_NS_LONG + "talvihoidonLuokka": "cid_talvihoidonluokka",
    CORE_NS_LONG + "puhtaanapitoluokka": "cid_puhtaanapitoluokkatyyppi",
    CORE_NS_LONG + "muutoshoitoluokka": "cid_muutoshoitoluokkatyyppi",
    CORE_NS_LONG + "sijaintiepavarmuus": "cid_sijaintiepavarmuustyyppi",
    CORE_NS_LONG + "luontitapa": "cid_luontitapatyyppi",
    "skip": "fid_osoite",
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

LOCATION_CREATION_ENUMERATION = {
    "digitointi": 1,
    "kiinteistötoimitus": 2,
    "kuvamittaus": 3,
    "laserkeilattu": 4,
    "maastomittaus": 5,
    "skannattu": 6,
    "tuntematon": 7,
    "muu": 8,
    "-1": 9,
}

LOCATION_UNCERTAINTY_ENUMERATION = {
    "0.15": 1,
    "0.2": 2,
    "0.3": 3,
    "0.5": 4,
    "0.7": 5,
    "1.0": 6,
    "1.5": 7,
    "2.0": 8,
    "3.0": 9,
    "5.0": 10,
    "7.5": 11,
    "10.0": 12,
    "20.0": 13,
    "-1": 14,
}

AREA_TAG_TO_TABLE = {
    CORE_NS_LONG + "kuuluuViheralueeseen": "viheralue",
    CORE_NS_LONG + "kuuluuKatualueeseen": "katualue",
    CORE_NS_LONG + "kuuluuViheralueenOsaan": "viheralueenosa",
    CORE_NS_LONG + "kuuluuKatuAlueenOsaan": "katualueenosa",
}

SRS_LIST = [
    "3067",
    "4326",
    "3857",
    "3873",
    "3874",
    "3875",
    "3876",
    "3877",
    "3878",
    "3879",
    "3880",
    "3881",
    "3882",
    "3883",
    "3884",
    "3885",
]

FORM_CLASS = load_ui('import.ui')
LOGGER = logging.getLogger(plugin_name())

def get_area_fids(conn_params):
    results_dicts = {"viheralueenosa": [],
                     "katualueenosa": [],
                     "viheralue": [],
                     "katualue": [],}
    for key in results_dicts.keys():
        if key.startswith('k'):
            schema = "katualue"
        else:
            schema = "viheralue"

        query = SQL("SELECT {}, {} FROM {}.{}").format(Identifier("fid"), Identifier("identifier"), Identifier(schema), Identifier(key))

        with(psycopg2.connect(**conn_params)) as conn:
            with conn.cursor() as curs:
                curs.execute(query)
                rows = curs.fetchall()
                result_dict = {}
                for row in rows:
                    result_dict[row[1]] = row[0]
                results_dicts[key] = result_dict
    return results_dicts


def add_enumeration_values(conn_params: dict, enumeration_tables: dict, column:str) -> dict:
    """
    Fetches an enumeration table corresponding a foreign key column and adds it to a dictionary for later use.

    Args:
        conn_params (dict): Connection parameters to the postgis database. 
        enumeration_tables (dict): Dictionary of dictionaries which will be updated with this function.
        column (str): The foreign key column whose corresponding enumeration table will be fetched.

    Returns:
        dict: A dictionary of dictionaries, where the keys are column names.
    """
    query = SQL("SELECT {}, {} FROM {}.{}").format(Identifier("selite"), Identifier("cid"), Identifier("koodistot"), Identifier(column.removeprefix('cid_')))
    with(psycopg2.connect(**conn_params)) as conn:
        with conn.cursor(cursor_factory=DictCursor) as curs:
            curs.execute(query)
            results = dict(curs.fetchall())
            enumeration_tables[column] = results
    return enumeration_tables


def add_shipment_information(conn_params:dict, tree:str) -> None:
    """
    Reads shipment information (aineistotoimituksen tiedot) from the gml file and adds it to the database.

    Args:
        conn_params (dict): Connection parameters to the postgis database. 
        tree (ET.ElementTree): XML tree.
    
    Returns:
        None
    """
    #tree = ET.parse(file_path)
    root = tree.getroot()

    shipment_grandparent = root.find(f".//{CORE_NS_LONG + 'toimituksentiedot'}")
    if shipment_grandparent is not None:
        shipment_information_elements = shipment_grandparent.findall("./*/*")
        if shipment_information_elements is not None:

            shipment_information_to_add = {}

            for element in shipment_information_elements:
                if element.tag in INFRAO_AINEISTOTOIMITUKSEN_TIEDOT.keys():
                    shipment_information_to_add[INFRAO_AINEISTOTOIMITUKSEN_TIEDOT[element.tag]] = element.text

            columns = SQL(', ').join(Identifier(column) for column in shipment_information_to_add)
            value_placeholders = SQL(', ').join(Placeholder() for _ in shipment_information_to_add)

            query = SQL("""
                INSERT INTO meta.aineistotoimituksentiedot ({columns})
                    VALUES ({value_placeholders})"""
                ).format(
                columns=columns,
                value_placeholders=value_placeholders)

            with(psycopg2.connect(**conn_params)) as conn:
                with conn.cursor(cursor_factory=DictCursor) as curs:
                    curs.execute(query, list(shipment_information_to_add.values()))


def add_decrees_and_their_attachments(conn_params:dict, decree_information_dicts:list) -> None: # TODO: refactor adding attachments etc. to a separate function
    """
    Adds decree (päätös) features and their linked attachments (if they exist).

    Args:
        conn_params (dict): Connection parameters to the postgis database. 
        decree_information_dicts (list): List of dictionaries for each decree, included is a list of potential attachments as dictionaries.

    Returns:
        None
    """
    for decree in decree_information_dicts:
        select_query = f"SELECT id FROM linkit.paatos WHERE kuvaus='{decree['kuvaus']}' AND paivamaarapvm='{decree['paivamaarapvm']}' AND fid_katualueenosa=(SELECT fid FROM katualue.katualueenosa WHERE identifier='{decree['feature_identifier']}' LIMIT 1)"
        select_query = SQL("""
            SELECT id
                FROM linkit.paatos
                WHERE kuvaus={kuvaus_value} AND
                      paivamaarapvm={paivamaarapvm} AND
                      fid_katualueenosa=(SELECT fid 
                                            FROM katualue.katualueenosa 
                                            WHERE identifier={feature_identifier_value} 
                                            LIMIT 1)
        """).format(
            kuvaus_value=Placeholder(),
            paivamaarapvm=Placeholder(),
            feature_identifier_value=Placeholder()
        )
        with(psycopg2.connect(**conn_params)) as conn:
            with conn.cursor() as curs:
                curs.execute(select_query, [decree['kuvaus'], decree['paivamaarapvm'], decree['feature_identifier']])
                select_result = curs.fetchone()

                decree_id = select_result[0] if select_result is not None else None

                if decree_id is None:
                    insert_query = SQL("""
                        INSERT INTO linkit.paatos (kuvaus, paivamaarapvm, fid_katualueenosa)
                        VALUES ({kuvaus_value}, {paivamaarapvm_value},
                        (SELECT fid FROM katualue.katualueenosa WHERE identifier={feature_identifier_value} LIMIT 1)
                        )
                        RETURNING id
                    """).format(
                        kuvaus_value=Placeholder(),
                        paivamaarapvm_value=Placeholder(),
                        feature_identifier_value=Placeholder()
                    )

                    curs.execute(insert_query, [decree['kuvaus'], decree['paivamaarapvm'], decree['feature_identifier']])

                    returning = curs.fetchone()

                    decree_id = returning[0]
        if decree['attachments'] is not []:
            for attachment_information_to_add in decree['attachments']:
                attachment_information_to_add['id_paatos'] = decree_id

                query = SQL("SELECT {columns} FROM {schema}.{table} WHERE {conditions}").format(
                    columns=SQL(", ").join(map(Identifier, ["fid"])),
                    schema=Identifier("linkit"),
                    table=Identifier("liite"),
                    conditions=SQL(" AND ").join(
                        Composed([Identifier(column), SQL("="), Placeholder()]) for column in attachment_information_to_add.keys()
                    )
                )
                with(psycopg2.connect(**conn_params)) as conn:
                    with conn.cursor() as curs:
                        curs.execute(query, list(attachment_information_to_add.values()))
                        result = curs.fetchone()

                        if result is None:
                            insert_columns = SQL(', ').join(Identifier(column) for column in attachment_information_to_add.keys())
                            insert_value_placeholders = SQL(', ').join(Placeholder() for _ in attachment_information_to_add.keys())
                            insert_query = SQL("""
                                INSERT INTO {schema}.{table} ({columns})
                                VALUES ({placeholders})
                            """).format(
                                schema=Identifier("linkit"),
                                table=Identifier("liite"),
                                columns=insert_columns,
                                placeholders=insert_value_placeholders)
                            curs.execute(insert_query, list(attachment_information_to_add.values()))


def add_plan_link_features(conn_params:dict, plan_link_dicts):
    """
    Insert plan link features to the database if a feature with the same attributes doesn't already exist.

    Args:
        conn_params (dict): Connection parameters to the postgis database. 
        plan_link_dicts (list): List of dictionaries for each plan link.
    
    Returns:
        None
    """
    for plan_link_dict in plan_link_dicts:
        for key in plan_link_dict:
            if key.startswith("fid_"):
                feature_identifier = plan_link_dict[key]
                feature_column = key
        with(psycopg2.connect(**conn_params)) as conn:
            with conn.cursor() as curs:
                if feature_column == "fid_viheralueenosa":
                    sub_schema = "viheralue"
                elif feature_column == "fid_katualueenosa" or feature_column == "fid_ajoratamerkinta":
                    sub_schema = "katualue"
                elif feature_column in ["fid_pysakointiruutu","fid_ymparistotaide","fid_rakenne", "fid_hulevesi"]:
                    sub_schema = "kohteet"
                else:
                    sub_schema = "varusteet"

                select_query = SQL(
                    """SELECT EXISTS (
                    SELECT 1 FROM linkit.suunnitelmalinkki
                    WHERE suunnitelmakohdeid={suunnitelmakohdeid_value}
                        AND fid_liite={fid_liite_value}
                        AND {feature_column}=(
                            SELECT fid FROM {sub_schema}.{sub_table}
                                WHERE identifier={feature_identifier} LIMIT 1
                            )
                        )"""
                    ).format(
                        suunnitelmakohdeid_value=Placeholder(),
                        fid_liite_value=Placeholder(),
                        feature_column=Identifier(feature_column),
                        sub_schema=Identifier(sub_schema),
                        sub_table=Identifier(key.removeprefix("fid_")),
                        feature_identifier=Placeholder()
                    )

                curs.execute(select_query, [plan_link_dict['suunnitelmakohdeid'], plan_link_dict['fid_liite'], feature_identifier])
                select_result = curs.fetchone()

                if select_result is not None:
                    feature_exists = select_result[0]
                if not feature_exists:
                    insert_query = SQL("""
                        INSERT INTO linkit.suunnitelmalinkki (suunnitelmakohdeid, fid_liite, {feature_column})
                            VALUES(
                            {suunnitelmakohdeid_value},
                            {fid_liite_value},
                            (SELECT fid FROM {sub_schema}.{sub_table} WHERE identifier={feature_identifier_value} LIMIT 1)
                            )"""
                        ).format(
                        feature_column=Identifier(feature_column),
                        suunnitelmakohdeid_value=Placeholder(),
                        fid_liite_value=Placeholder(),
                        sub_schema=Identifier(sub_schema),
                        sub_table=Identifier(key.removeprefix("fid_")),
                        feature_identifier_value = Placeholder()
                        )
                    curs.execute(insert_query, [plan_link_dict["suunnitelmakohdeid"], plan_link_dict["fid_liite"], feature_identifier])


def get_values_from_xml(table: str, tree: ET.ElementTree, results_dicts:dict, conn_params:dict, enumeration_tables:dict, plan_link_dicts:list, decree_information_dicts:list, import_from_api:bool) -> tuple[list, dict, list, list]:
    """
    Main loop for iterating over the gml file and reading the elements table by table and retrieving their values to be used in building the insert query later.

    Args:
        table (str): Name of the table being iterated over.
        tree (ET.ElementTree): XML tree.
        results_dicts(dict): Dictionary containing which elements belong to are elements (katualue etc.)
        conn_params (dict): Connection parameters to the postgis database. 
        enumeration_tables (dict): Dictionary of dictionaries for reading values and if needed adding for enumeration tables.
        plan_link_dicts (list): List of plan link features to be added later being updated in this function.
        decree_information_dicts (list): List of decree features to be added later.
        import_from_api (bool): True if importing from api, false if importing from file.

    Returns:
        A tuple containing the following variables:
        - values_dict: list of dictionaries for each feature of the element type being iterated over.
        - enumeration_tables: updated dictionary of dictionaries containing cached enumeration tables.
        - plan_link_dicts: Updated list of plan link features to be added later.
        - decree_information_dicts: Updated list of decree features to be added later.
    """
    element = TABLE_TO_ELEMENT[table][0]
    element_dict = TABLE_TO_ELEMENT[table][1]

    root = tree.getroot()

    values_dict = []

    if import_from_api:
        f_members = root.findall("{http://www.opengis.net/wfs/2.0}member")
        if f_members == []:
            f_members = root.findall("{http://www.opengis.net/ogcapi-features-1/1.0/sf}featureMember")

        features = []

        for f_member in f_members:
            f_member_children = f_member.findall(f"./{element}") # TODO: search by tag?
            for f_member_child in f_member_children:
                features.append(f_member_child)
    else:
        features = root.findall(f".//{element}")

    tags = list(element_dict.keys())

    if table != "katualue" or table != "viheralue":
        tags.extend(SIJAINTI_TAGS)

    for feature in features:
        value_dict = {key: "-1" if key.startswith("cid_") else None for key in element_dict.values() if key != "skip"}
        for tag in tags:
            children = feature.findall(f"./{tag}")
            if children is not None:
                for child in children:
                    if child.text == None or len(element) > 0:
                        if not child.tag in [CORE_NS_LONG + "paatostieto", CORE_NS_LONG + "suunnitelmalinkkitieto", CORE_NS_LONG + "metatieto", CORE_NS_LONG + "kuuluuKatualueeseen", CORE_NS_LONG + "kuuluuViheralueeseen", CORE_NS_LONG + "kuuluuKatuAlueenOsaan", CORE_NS_LONG + "kuuluuViheralueenOsaan", CORE_NS_LONG + "tarkkaSijaintitieto", CORE_NS_LONG + "sijaintitieto", CORE_NS_LONG + "sijainti",]:
                            column = element_dict[child.tag]
                            value = child.text
                            if column.startswith('cid_'):
                                enumeration_dict = enumeration_tables.get(column)
                                if enumeration_dict is None:
                                    enumeration_tables = add_enumeration_values(conn_params, enumeration_tables, column)
                                    enumeration_dict = enumeration_tables[column]
                                try:
                                    value = enumeration_tables[column][value]
                                except KeyError:
                                    value = -1
                                    LOGGER.info(f'Kohteen "{feature.tag}.{value_dict.get(element_dict[CORE_NS_LONG + "yksilointitieto"])}" enumeraatioarvo "{child.text}" kentässä "{child.tag}" ei löytynyt.')
                            value_dict[element_dict[child.tag]] = value
                        elif child.tag == CORE_NS_LONG + "metatieto":
                            meta_children = child.findall("./gml:metaDataProperty/gml:GenericMetaData/*", GML_NS_LONG_DICT)
                            if meta_children is not None:
                                for meta_child in meta_children:
                                    value_dict[element_dict[meta_child.tag]] = meta_child.text
                        elif child.tag == CORE_NS_LONG + "paatostieto":
                            decree_information_dict = {}

                            decree_description = child.find(f"./*/{CORE_NS_LONG + 'kuvaus'}")
                            decree_description_value = decree_description.text if decree_description is not None else None
                            
                            decree_date = child.find(f"./*/{CORE_NS_LONG + 'paivamaaraPvm'}")
                            decree_date_value = decree_date.text if decree_date is not None else None

                            decree_information_dict['kuvaus'] = decree_description_value
                            decree_information_dict['paivamaarapvm'] = decree_date_value

                            attachments = child.findall(f"./*/{CORE_NS_LONG + 'liitetieto'}/*")

                            attachment_list = []

                            if attachments is not None:
                                for attachment in attachments:
                                    attachment_information_to_add = {key: None for key in INFRAO_LIITE_TAGS.values()}
                                    for attachment_field in attachment:
                                        attachment_information_to_add[INFRAO_LIITE_TAGS[attachment_field.tag]] = attachment_field.text
                                    attachment_list.append(attachment_information_to_add)

                            decree_information_dict["feature_identifier"] = value_dict["identifier"]
                            decree_information_dict["attachments"] = attachment_list

                            decree_information_dicts.append(decree_information_dict)
                        elif child.tag == CORE_NS_LONG + "suunnitelmalinkkitieto":
                            plan_link_dict = {}
                            attachment = child.find(f"./*/{CORE_NS_LONG + 'liitetieto'}/*")
                            if attachment is not None:
                                attachment_information_to_add = {key: None for key in INFRAO_LIITE_TAGS.values()}
                                for attachment_field in attachment:
                                    attachment_information_to_add[INFRAO_LIITE_TAGS[attachment_field.tag]] = attachment_field.text
                                query = SQL("SELECT {columns} FROM {schema}.{table} WHERE {conditions}").format(
                                    columns=SQL(", ").join(map(Identifier, ["fid"])),
                                    schema=Identifier("linkit"),
                                    table=Identifier("liite"),
                                    conditions=SQL(" AND ").join(
                                        Composed([Identifier(column), SQL("="), Placeholder()]) for column in attachment_information_to_add.keys()
                                    )
                                )
                                with(psycopg2.connect(**conn_params)) as conn:
                                    with conn.cursor() as curs:
                                        curs.execute(query, list(attachment_information_to_add.values()))
                                        result = curs.fetchone()

                                        if result is not None:
                                            attachment_fid = result[0]
                                            plan_link_dict["fid_liite"] = attachment_fid
                                        else:
                                            insert_columns = SQL(', ').join(Identifier(column) for column in attachment_information_to_add.keys())
                                            insert_value_placeholders = SQL(', ').join(Placeholder() for _ in attachment_information_to_add.keys())
                                            insert_query = SQL("""
                                                INSERT INTO {schema}.{table} ({columns})
                                                VALUES ({placeholders})
                                                RETURNING fid;
                                            """).format(
                                                schema=Identifier("linkit"),
                                                table=Identifier("liite"),
                                                columns=insert_columns,
                                                placeholders=insert_value_placeholders)
                                            curs.execute(insert_query, list(attachment_information_to_add.values()))

                                            inserted_result = curs.fetchone()

                                            if inserted_result is not None:
                                                inserted_attachment_fid = inserted_result[0]
                                                plan_link_dict["fid_liite"] = inserted_attachment_fid
                            plan_link_id_element = child.find(f'./*/{CORE_NS_LONG + "suunnitelmakohdeId"}')
                            if plan_link_id_element is not None:
                                plan_link_dict["suunnitelmakohdeid"] = plan_link_id_element.text
                            feature_identifier = value_dict["identifier"]
                            plan_link_dict[f"fid_{table}"] = feature_identifier
                            plan_link_dicts.append(plan_link_dict)
                        elif child.tag in SIJAINTI_TAGS or table == 'keskilinja' and child.tag == CORE_NS_LONG + "sijainti":
                            gml_elem = None
                            geom = None
                            if table != "keskilinja":
                                sij_creation = child.find(f"./*/{CORE_NS_LONG}luontitapa")
                                sij_uncertainty = child.find(f"./*/{CORE_NS_LONG}sijaintiepavarmuus")

                                if sij_creation is not None:
                                    value_dict[element_dict[sij_creation.tag]] = LOCATION_CREATION_ENUMERATION[sij_creation.text]

                                if sij_uncertainty is not None:
                                    value_dict[element_dict[sij_uncertainty.tag]] = LOCATION_UNCERTAINTY_ENUMERATION[sij_uncertainty.text]

                                for sij_child in child:
                                    for geom_type in INFRAO_GEOMS:
                                        io_geom_element = sij_child.find(f"./{geom_type}")
                                        if io_geom_element is not None:
                                            sij_key = io_geom_element.tag

                                            gml_elem = io_geom_element.find('*')

                                address = child.find(f"./*/{CORE_NS_LONG}osoitetieto")

                                if address is not None:
                                    address_fields = address.findall(f"./*/*")

                                    if address_fields is not None:
                                        address_information_to_add = {key: None for key in INFRAO_OSOITE_TAGS.values() if not key.startswith("geom_")}

                                        for address_field in address_fields:
                                            if address_field.tag != CORE_NS_LONG + "nimitieto" and address_field.tag not in [CORE_NS_LONG + "pistesijainti", CORE_NS_LONG + "aluesijainti", CORE_NS_LONG + "viivasijainti",]:
                                                address_information_to_add[INFRAO_OSOITE_TAGS[address_field.tag]] = address_field.text
                                            elif address_field.tag == CORE_NS_LONG + "nimitieto":
                                                name_information = address_field.find(f"./*/*")
                                                address_information_to_add[INFRAO_OSOITE_TAGS[address_field.tag]] = name_information.text

                                        query = SQL("SELECT {columns} FROM {schema}.{table} WHERE {conditions}").format(
                                                        columns=SQL(", ").join(map(Identifier, ["fid"])),
                                                        schema=Identifier("osoite"),
                                                        table=Identifier("osoite"),
                                                        conditions=SQL(" AND ").join(
                                                            Composed([Identifier(column), SQL("="), Placeholder()]) for column, value in address_information_to_add.items() if value is not None
                                                        )
                                                    )
                                        
                                        with(psycopg2.connect(**conn_params)) as conn:
                                            with conn.cursor(cursor_factory=DictCursor) as curs:
                                                query_values = [value for value in address_information_to_add.values() if value is not None]
                                                curs.execute(query, query_values)
                                                result = curs.fetchone()

                                                if result is not None:
                                                    address_fid = result[0]
                                                    value_dict["fid_osoite"] = address_fid
                                                else:
                                                    insert_columns = SQL(', ').join(Identifier(column) for column, value in address_information_to_add.items() if value is not None)
                                                    insert_value_placeholders = SQL(', ').join(Placeholder() for value in address_information_to_add.values() if value is not None)
                                                    insert_query = SQL("""
                                                        INSERT INTO {schema}.{table} ({columns})
                                                        VALUES ({placeholders})
                                                        RETURNING fid;
                                                    """).format(
                                                        schema=Identifier("osoite"),
                                                        table=Identifier("osoite"),
                                                        columns=insert_columns,
                                                        placeholders=insert_value_placeholders)
                                                    curs.execute(insert_query, query_values)

                                                    inserted_result = curs.fetchone()

                                                    if inserted_result is not None:
                                                        inserted_address_fid = inserted_result[0]
                                                        value_dict["fid_osoite"] = inserted_address_fid
                            else:
                                gml_elem = child.find('*')
                                sij_key = child.tag
                            if gml_elem is not None:
                                gml_string = ET.tostring(gml_elem).decode('utf-8')
                                geom = ogr.CreateGeometryFromGML(gml_string)
                            if geom is not None:
                                geom_type = geom.GetGeometryType()
                                if geom_type == 1010 or geom_type == 10:
                                    geom = ogr.ForceToPolygon(geom)
                                if geom_type == 9 or geom_type == 1009 or geom_type == 8 or geom_type == 1008:
                                    geom = ogr.ForceToLineString(geom)
                                geom_wkb = geom.ExportToWkb()
                                if "srsName" in gml_elem.attrib:
                                    match = next((srs for srs in SRS_LIST if srs in gml_elem.attrib["srsName"]), None)
                                    if match is None:
                                        match = "4326"
                                    
                                    source_crs = QgsProject.instance().crs().fromEpsgId(int(match))
                                    target_crs = QgsProject.instance().crs().fromEpsgId(SYSTEM_EPSG)

                                    qgs_geom = QgsGeometry()
                                    qgs_geom.fromWkb(geom_wkb)
                                    transform = QgsCoordinateTransform(source_crs, target_crs, QgsProject.instance())

                                    qgs_geom.transform(transform)
                                    
                                    geom_wkb = bytes(qgs_geom.asWkb())
                                geom.Set3D(True)
                                try:
                                    value_dict[element_dict[sij_key]] = geom_wkb
                                except:
                                    LOGGER.info(f"Ongelma kohteen {feature.tag}.{value_dict.get(element_dict[CORE_NS_LONG + 'yksilointitieto'])} geometrian lisäämisessä.")
                            else:
                                LOGGER.info(f"Ongelma kohteen {feature.tag}.{value_dict.get(element_dict[CORE_NS_LONG + 'yksilointitieto'])} geometrian lukemisessa.")
                                pass
                        elif child.tag.startswith(CORE_NS_LONG + "kuuluu"):
                            try:
                                belong_attrib = child.attrib[XLINK_NS_LONG + "href"]
                                dot_pos = belong_attrib.find('.')
                                if dot_pos != -1:
                                    id = belong_attrib[dot_pos + 1:]
                                    try:
                                        value_dict[element_dict[child.tag]] = results_dicts[AREA_TAG_TO_TABLE[child.tag]][id]
                                    except:
                                        LOGGER.info(f"Kohteen {feature.tag}.{value_dict.get(element_dict[CORE_NS_LONG + 'yksilointitieto'])} sisältävän alueen yksilöintitietoa ei löytynyt.")
                                        pass
                            except KeyError:
                                LOGGER.info(f"Kohteen {feature.tag} elementti {child.tag} ei sisällä xlink- attribuuttia.")
                                pass
        values_dict.append(value_dict)
    return values_dict, enumeration_tables, plan_link_dicts, decree_information_dicts


def build_sql_query(values_dict:list, schema:str, table:str) -> tuple[Composed, list]:
    """
    Builds an SQL query based on the value list iteratively which adds all features to the table.

    Args:
        values_dict (list): List of dictionaries for each feature to be added to the table.
        schema (str): Name of the table's schema being inserted into.
        table (str): Name of the table being inserted into.
    
    Returns:
        A tuple containing the following variables:
        - query: The query as an psycopg2.sql.Composed object.
        - values: List of the values to be inserted.
    """
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


def add_features_to_database(query:Composed, values:list, conn_params:dict):
    """
    Executes the insert query.

    Args:
        query (Composed): The query that inserts features to the database.
        values (list): The values being inserted.
        conn_params (dict): Connection parameters to the postgis database. 

    """
    with(psycopg2.connect(**conn_params)) as conn:
        with conn.cursor() as curs:
            #LOGGER.info(query.as_string(curs)) #TODO: remove
            #LOGGER.info(values)
            curs.execute(query, values)


def xml_import(conn_params: dict, tree:ET.ElementTree, import_from_api:bool):
    """
    Main function for running the previous functions.

    Args:
        conn_params (dict): Connection parameters to the postgis database.
        tree (ET.ElementTree): XML tree.
        import_from_api (bool): True if importing from api, false if importing from file.
    
    Returns:
        None
    """
    start = time.time()
    LOGGER.info("========================================XML IMPORT STARTED========================================")
    enumeration_tables = {}
    plan_link_dicts = []
    decree_information_dicts = []

    # Iterate over the tables in this order so primary keys have been generated for related tables and update the area fid dictionary accordingly.

    for schema, table in AREA_TABLE_LIST:
        values_dict, enumeration_tables, _, _ = get_values_from_xml(table, tree, None, conn_params, enumeration_tables, plan_link_dicts, decree_information_dicts, import_from_api)
        if not values_dict == []:
            #LOGGER.info(f"Yritetään lisätä kohteita tauluun: {table}")
            query, values = build_sql_query(values_dict, schema, table)
            add_features_to_database(query, values, conn_params)
            #LOGGER.info(f"Kohteet lisätty tauluun: {table}")
    results_dicts = get_area_fids(conn_params)

    for schema, table in AREA_PART_TABLE_LIST:
        values_dict, enumeration_tables, plan_link_dicts, decree_information_dicts = get_values_from_xml(table, tree, results_dicts, conn_params, enumeration_tables, plan_link_dicts, decree_information_dicts, import_from_api)
        if not values_dict == []:
            #LOGGER.info(f"Yritetään lisätä kohteita tauluun: {table}")
            query, values = build_sql_query(values_dict, schema, table)
            add_features_to_database(query, values, conn_params)
            #LOGGER.info(f"Kohteet lisätty tauluun: {table}")
    results_dicts = get_area_fids(conn_params)

    for schema, table in TABLE_LIST:
        values_dict, enumeration_tables, plan_link_dicts, _ = get_values_from_xml(table, tree, results_dicts, conn_params, enumeration_tables, plan_link_dicts, decree_information_dicts, import_from_api)
        if not values_dict == []:
            #LOGGER.info(f"Yritetään lisätä kohteita tauluun: {table}")
            query, values = build_sql_query(values_dict, schema, table)
            add_features_to_database(query, values, conn_params)
            #LOGGER.info(f"Kohteet lisätty tauluun: {table}")

    # Add plan link and decree features and their attachments last so main feature primary keys have been generated.

    add_plan_link_features(conn_params, plan_link_dicts)
    add_decrees_and_their_attachments(conn_params, decree_information_dicts)
    add_shipment_information(conn_params, tree)

    # Refresh the QGIS canvas to see added features.

    canvas = iface.mapCanvas()
    canvas.refreshAllLayers()

    end = time.time()
    LOGGER.info("========================================XML IMPORT ENDED  ========================================")
    LOGGER.info(f"TIME ELAPSED: {round(((end-start) * 10**3)/1000, 2)} seconds.")
    iface.messageBar().pushMessage(f"Kohteet tiedostosta {tree} tuotu onnistuneesti tietokantaan.", level=3, duration=10)