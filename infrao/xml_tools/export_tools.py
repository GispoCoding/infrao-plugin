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
import traceback

import psycopg2
from psycopg2.sql import SQL, Identifier, Placeholder
from psycopg2.extras import DictCursor

import time

import xml.etree.ElementTree as ET

from qgis.core import NULL
from qgis.utils import iface

from ..qgis_plugin_tools.tools.resources import plugin_name



CORE_NS = "infrao"

# infrao element tags
INFRAO_KOHTEET = CORE_NS + ":InfraoKohteet"
INFRAO_AJORATAMERKINTA = CORE_NS + ":Ajoratamerkinta"
INFRAO_ERIKOISRAKENNEKERROS = CORE_NS + ":ErikoisrakenneKerros"
INFRAO_HULEVESI = CORE_NS + ":Hulevesi"
INFRAO_JATE = CORE_NS + ":Jate"
INFRAO_KALUSTE = CORE_NS + ":Kaluste"
INFRAO_KATUALUE = CORE_NS + ":Katualue"
INFRAO_KATUALUEENOSA = CORE_NS + ":KatualueenOsa"
INFRAO_KESKILINJA = CORE_NS + ":Keskilinja"
INFRAO_LEIKKIVALINE = CORE_NS + ":Leikkivaline"
INFRAO_LIIKENNEMERKKI = CORE_NS + ":Liikennemerkki"
INFRAO_LIIKUNTA = CORE_NS + ":Liikunta"
INFRAO_LIITE = CORE_NS + ":Liite"
INFRAO_MELU = CORE_NS + ":Melu"
INFRAO_MUUKASVI = CORE_NS + ":MuuKasvi"
INFRAO_MUUVARUSTE = CORE_NS + ":MuuVaruste"
INFRAO_NIMI = CORE_NS + ":Nimi"
INFRAO_OPASTE = CORE_NS + ":Opaste"
INFRAO_OSOITE = CORE_NS + ":Osoite"
INFRAO_PAATOS = CORE_NS + ":Paatos"
INFRAO_PUU = CORE_NS + ":Puu"
INFRAO_PYSAKOINTIRUUTU = CORE_NS + ":Pysakointiruutu"
INFRAO_RAKENNE = CORE_NS + ":Rakenne"
INFRAO_SIJAINTI = CORE_NS + ":Sijainti"
INFRAO_SUUNNITELMA = CORE_NS + ":Suunnitelma"
INFRAO_SUUNNITELMALINKKI = CORE_NS + ":Suunnitelmalinkki"
INFRAO_VIHERALUE = CORE_NS + ":Viheralue"
INFRAO_VIHERALUEENOSA = CORE_NS + ":ViheralueenOsa"
INFRAO_YMPARISTOTAIDE = CORE_NS + ":Ymparistotaide"

INFRAO_AINEISTOTOIMITUKSEN_TIEDOT = {
    "aineistonnimi": CORE_NS + ":aineistonnimi",
    "aineistotoimittaja": CORE_NS + ":aineistotoimittaja",
    "tila": CORE_NS + ":tila",
    "toimituspvm": CORE_NS + ":toimitusPvm",
    "kuntakoodi": CORE_NS + ":kuntakoodi",
    "kielitieto": CORE_NS + ":kielitieto",
    "metatietotunniste": CORE_NS + ":metatietotunniste",
    "metatietoxmlurl": CORE_NS + ":metatietoXMLURL",
    "metatietourl": CORE_NS + ":metatietoURL",
    "tietotuoteurl": CORE_NS + ":tietotuoteURL",
}

AINEISTO_TILA = [None, "valmis", "keskeneräinen", "muu", "ei tiedossa"]


# infrao area element list
INFRAO_AREA_ELEMENTS = [
        INFRAO_KATUALUE,
        INFRAO_VIHERALUE,
        INFRAO_VIHERALUEENOSA,
        INFRAO_KATUALUEENOSA]

# infrao abstractpaikkatietopalvelukohde tags
INFRAO_ABSTRACT_PAIKKATIETOPALVELUKOHDE = {
    "FID": ["", "fid"],
    "METATIETO": [CORE_NS + ":metatieto", "skip"],
    "META_DATANLUOJA": ["datan_luoja", "meta_datanluoja"],
    "META_MUOKKAAJA": ["muokkaaja", "meta_muokkaaja"],
    "META_MUOKKAUSPVM": ["muokkaus_pvm", "meta_muokkauspvm"],
    "META_OMISTAJA": ["omistaja", "meta_omistaja"],
    "META_LAHTEENPVM": ["lahteen_pvm", "meta_lahteenpvm"],
    "META_MITTAUSERA": ["mittausera", "meta_mittausera"],
    "META_LISATIETOLINKKI": ["lisatieto_linkki", "meta_lisatietolinkki"],
    "YKSILOINTITIETO": [CORE_NS + ":yksilointitieto", "identifier"],
    "ALKUHETKI": [CORE_NS + ":alkuHetki", "alkuhetki"],
    "LOPPUHETKI": [CORE_NS + ":loppuHetki", "loppuhetki"]
}

# infrao abstractvaruste tags
INFRAO_ABSTRACT_VARUSTE = {
    "GEOM_POINT": [CORE_NS + ":tarkkaSijaintitieto", "geom_point"],
    "GEOM_LINE": [CORE_NS + ":tarkkaSijaintitieto", "geom_line"], 
    "TARKKASIJAINTITIETO": [CORE_NS + ":tarkkaSijaintitieto", "geom_poly"],
    "OMISTAJA": [CORE_NS + ":omistaja", "omistaja"],
    "HALTIJA": [CORE_NS + ":haltija", "haltija"],
    "KUNNOSSAPITAJA": [CORE_NS + ":kunnossapitaja", "kunnossapitaja"],
    "MALLI": [CORE_NS + ":malli", "malli"],
    "PERUSPARANNUSVUOSI": [CORE_NS + ":perusparannusvuosi", "perusparannusvuosi"],
    "SUUNTA": [CORE_NS + ":suunta", "suunta"],
    "VALMISTAJA": [CORE_NS + ":valmistaja", "valmistaja"],
    "VALMISTUMISVUOSI": [CORE_NS + ":valmistumisvuosi", "valmistumisvuosi"],
    "MATERIAALI": [CORE_NS + ":materiaali", "cid_varustemateriaali"],
    "SUUNNITELMALINKKITIETO": [CORE_NS + ":suunnitelmalinkkitieto", "skip"],
    "KUULUUVIHERALUEENOSAAN": [CORE_NS + ":kuuluuViheralueenOsaan", "fid_viheralueenosa"],
    "KUULUUKATUALUEENOSAAN": [CORE_NS + ":kuuluuKatuAlueenOsaan", "fid_katualueenosa"],
    "LUONTITAPA": [CORE_NS + ":luontitapa", "cid_luontitapatyyppi"],
    "OSOITE": [CORE_NS + ":osoitetieto", "fid_osoite"],
    "SIJAINTIEPAVARMUUS": [CORE_NS + ":sijaintiepavarmuus", "cid_sijaintiepavarmuustyyppi"],
}

# infrao abstractkasvillisuus tags
INFRAO_ABSTRACT_KASVILLISUUS = {
    "OMISTAJA": [CORE_NS + ":omistaja", "omistaja"],
    "HALTIJA": [CORE_NS + ":haltija", "haltija"],
    "KUNNOSSAPITAJA": [CORE_NS + ":kunnossapitaja", "kunnossapitaja"],
    "GEOM_POINT": [CORE_NS + ":sijaintitieto", "geom_point"],
    "GEOM_LINE": [CORE_NS + ":sijaintitieto", "geom_line"], 
    "SIJAINTITIETO": [CORE_NS + ":sijaintitieto", "geom_poly"],
    "KUULUUVIHERALUEENOSAAN": [CORE_NS + ":kuuluuViheralueenOsaan", "fid_viheralueenosa"],
    "KUULUUKATUALUEENOSAAN": [CORE_NS + ":kuuluuKatuAlueenOsaan", "fid_katualueenosa"],
    "LUONTITAPA": [CORE_NS + ":luontitapa", "cid_luontitapatyyppi"],
    "OSOITE": [CORE_NS + ":osoitetieto", "fid_osoite"],
    "SIJAINTIEPAVARMUUS": [CORE_NS + ":sijaintiepavarmuus", "cid_sijaintiepavarmuustyyppi"],
}

## ELEMENT TAGS
# infrao:Ajoratamerkinta unique tags -> inherit abstractpaikkatietopalvelukohde and abstractvaruste
INFRAO_AJORATAMERKINTA_TAGS = {}
INFRAO_AJORATAMERKINTA_TAGS |= INFRAO_ABSTRACT_PAIKKATIETOPALVELUKOHDE
INFRAO_AJORATAMERKINTA_TAGS |= INFRAO_ABSTRACT_VARUSTE
INFRAO_AJORATAMERKINTA_TAGS |= {
    "JYRSITTYPINTAKYTKIN": [CORE_NS + ":jyrsittyPintaKytkin", "jyrsittypinta_kytkin"],
    "TYYPPI": [CORE_NS + ":tyyppi", "cid_ajoratamerkintatyyppi"]
}


# infrao:ErikoisrakenneKerros -> inherit abstractpaikkatietopalvelukohde
INFRAO_ERIKOISRAKENNEKERROS_TAGS = {}
INFRAO_ERIKOISRAKENNEKERROS_TAGS |= INFRAO_ABSTRACT_PAIKKATIETOPALVELUKOHDE
INFRAO_ERIKOISRAKENNEKERROS_TAGS |= {
    "OMISTAJA": [CORE_NS + ":omistaja", "omistaja"],
    "HALTIJA": [CORE_NS + ":haltija", "haltija"],
    "KUNNOSSAPITAJA": [CORE_NS + ":kunnossapitaja", "kunnossapitaja"],
    "SELITE": [CORE_NS + ":selite", "erk_selite"],
    "MATERIAALI": [CORE_NS + ":materiaali", "materiaali"],
    "TYYPPI": [CORE_NS + ":tyyppi", "cid_erikoisrakennekerrosmateriaalityyppi"],
    "GEOM_POINT": [CORE_NS + ":sijainti", "geom_point"],
    "GEOM_LINE": [CORE_NS + ":sijainti", "geom_line"], 
    "SIJAINTI": [CORE_NS + ":sijainti", "geom_poly"],
    "LUONTITAPA": [CORE_NS + ":luontitapa", "cid_luontitapatyyppi"],
    "SIJAINTIEPAVARMUUS": [CORE_NS + ":sijaintiepavarmuus", "cid_sijaintiepavarmuustyyppi"],
}


# infrao:Hulevesi unique tags -> inherit abstractpaikkatietopalvelukohde and abstractvaruste
INFRAO_HULEVESI_TAGS = {}
INFRAO_HULEVESI_TAGS |= INFRAO_ABSTRACT_PAIKKATIETOPALVELUKOHDE
INFRAO_HULEVESI_TAGS |= INFRAO_ABSTRACT_VARUSTE
INFRAO_HULEVESI_TAGS |= {
    "HULEVESI": [CORE_NS + ":hulevesi", "cid_hulevesityyppi"]
}


# infrao:InfraoKohteet unique tags
INFRAO_INFRAOKOHTEET_TAGS = { #TODO: remove if not needed
    "TOIMITUKSENTIEDOT": [CORE_NS + ":toimituksentiedot"]
}

# infrao:Jate unique tags -> inherit abstractpaikkatietopalvelukohde and abstractvaruste
INFRAO_JATE_TAGS = {}
INFRAO_JATE_TAGS |= INFRAO_ABSTRACT_PAIKKATIETOPALVELUKOHDE
INFRAO_JATE_TAGS |= INFRAO_ABSTRACT_VARUSTE
INFRAO_JATE_TAGS |= {
    "KOKO": [CORE_NS + ":koko", "koko"],
    "PUTKIKERAYSJARJESTELMAKYTKIN": [CORE_NS + ":putkikeraysjarjestelmaKytkin", "putkikeraysjarjestelma_kytkin"],
    "SIJAINTIMAANPINNALLAKYTKIN": [CORE_NS + ":sijaintiMaanPinnallaKytkin", "sijaintimaanpinnalla_kytkin"],
    "VAARALLISTENJATEASTIAKYTKIN":[CORE_NS + ":vaarallistenJateastiaKytkin", "vaarallistenjateastia_kytkin"],
    "JATE": [CORE_NS + ":jate", "cid_jatetyyppi"]
}


# infrao:Kaluste unique tags -> inherit abstractpaikkatietopalvelukohde and abstractvaruste
INFRAO_KALUSTE_TAGS = {}
INFRAO_KALUSTE_TAGS |= INFRAO_ABSTRACT_PAIKKATIETOPALVELUKOHDE
INFRAO_KALUSTE_TAGS |= INFRAO_ABSTRACT_VARUSTE
INFRAO_KALUSTE_TAGS |= {
    "KALUSTE": [CORE_NS + ":kaluste", "cid_kalustetyyppi"]
}

# infrao:Katualue unique tags -> inherit abstractpaikkatietopalvelukohde
INFRAO_KATUALUE_TAGS = {}
INFRAO_KATUALUE_TAGS |= INFRAO_ABSTRACT_PAIKKATIETOPALVELUKOHDE
INFRAO_KATUALUE_TAGS |= {
    "SISALTAAKATUALUEENOSAN": [CORE_NS + ":sisaltaaKatualueenOsan", "skip"],
    "NIMI": [CORE_NS + ":nimi", "nimi"]
}

# infrao:KatualueenOsa unique tags -> inherit abstractpaikkatietopalvelukohde
INFRAO_KATUALUEENOSA_TAGS = {}
INFRAO_KATUALUEENOSA_TAGS |= INFRAO_ABSTRACT_PAIKKATIETOPALVELUKOHDE
INFRAO_KATUALUEENOSA_TAGS |= {
    "PAATOSTIETO": [CORE_NS + ":paatostieto", "skip"],
    "OMISTAJA": [CORE_NS + ":omistaja", "omistaja"], 
    "HALTIJA": [CORE_NS + ":haltija", "haltija"], 
    "KUNNOSSAPITAJA": [CORE_NS + ":kunnossapitaja", "kunnossapitaja"], 
    "KUNNOSSAPITO": [CORE_NS + ":kunnossapito", "kunnossapito"],
    "LEVEYS": [CORE_NS + ":leveys", "leveys"],
    "PERUSPARANNUSVUOSI": [CORE_NS + ":perusparannusvuosi", "perusparannusvuosi"], 
    "PINTAALA": [CORE_NS + ":pintaAla", "pinta_ala"],
    "PITUUS": [CORE_NS + ":pituus", "pituus"],
    "PUHTAANAPITO": [CORE_NS + ":puhtaanapito", "puhtaanapito"],
    "TALVIKUNNOSSAPITO": [CORE_NS + ":talvikunnossapito", "talvikunnossapito"],
    "VALMISTUMISVUOSI": [CORE_NS + ":valmistumisvuosi", "valmistumisvuosi"], 
    "KUULUUKATUALUEESEEN": [CORE_NS + ":kuuluuKatualueeseen", "fid_katualue"],
    "SISALTAAKESKILINJA": [CORE_NS + ":sisaltaaKeskilinja", "skip"],
    "LUOKKA": [CORE_NS + ":luokka", "cid_toiminnallinenluokka"],
    "LAJI": [CORE_NS + ":laji", "cid_katuosanlaji"],
    "VIHERALUEENLAJI": [CORE_NS + ":viheralueenLaji", "cid_viherosanlajityyppi"],
    "PINTAMATERIAALI": [CORE_NS + ":pintamateriaali", "cid_pintamateriaali"],
    "KUNNOSSAPITOLUOKKA": [CORE_NS + ":kunnossapitoluokka", "cid_hoitoluokkatyyppi"],
    "SIJAINTITIETO": [CORE_NS + ":sijaintitieto", "geom"], 
    "SUUNNITELMALINKKITIETO": [CORE_NS + ":suunnitelmalinkkitieto", "skip"],
    "TALVIHOIDONLUOKKA": [CORE_NS + ":talvihoidonLuokka", "cid_talvihoidonluokka"],
    "SISALTAAKASVILLISUUS": [CORE_NS + ":sisaltaaKasvillisuus", "skip"],
    "SISALTAAVARUSTE": [CORE_NS + ":sisaltaaVaruste", "skip"],
    "LUONTITAPA": [CORE_NS + ":luontitapa", "cid_luontitapatyyppi"],
    "OSOITE": [CORE_NS + ":osoitetieto", "fid_osoite"],
    "SIJAINTIEPAVARMUUS": [CORE_NS + ":sijaintiepavarmuus", "cid_sijaintiepavarmuustyyppi"],
}


# infrao:Keskilinja unique tags -> inherit abstractpaikkatietopalvelukohde
INFRAO_KESKILINJA_TAGS = {}
INFRAO_KESKILINJA_TAGS |= INFRAO_ABSTRACT_PAIKKATIETOPALVELUKOHDE
INFRAO_KESKILINJA_TAGS |= {
    "DIGIROADID": [CORE_NS + ":DigiroadID", "digiroadid"],
    "SIJAINTI": [CORE_NS + ":sijainti", "geom"],
    "KUULUUKATUALUEENOSAAN": [CORE_NS + ":kuuluuKatualueenOsaan", "fid_katualueenosa"],
}


# infrao:Leikkivaline unique tags -> inherit abstractpaikkatietopalvelukohde and abstractvaruste
INFRAO_LEIKKIVALINE_TAGS = {}
INFRAO_LEIKKIVALINE_TAGS |= INFRAO_ABSTRACT_PAIKKATIETOPALVELUKOHDE
INFRAO_LEIKKIVALINE_TAGS |= INFRAO_ABSTRACT_VARUSTE
INFRAO_LEIKKIVALINE_TAGS |= {
    "TOIMINNALLINENTARKASTUSPVM": [CORE_NS + ":toiminnallinenTarkastusPvm", "toiminnallinentarkastus_pvm"],
    "VUOSITARKASTUSPVM": [CORE_NS + ":vuositarkastusPvm", "vuositarkastus_pvm"],
    "LEIKKIVALINE": [CORE_NS + ":leikkivaline", "cid_leikkivalinetyyppi"]
}

# infrao:Liikennemerkki tags -> inherit abstractpaikkatietopalvelukohde and abstractvaruste
INFRAO_LIIKENNEMERKKI_TAGS = {}
INFRAO_LIIKENNEMERKKI_TAGS |= INFRAO_ABSTRACT_PAIKKATIETOPALVELUKOHDE
INFRAO_LIIKENNEMERKKI_TAGS |= INFRAO_ABSTRACT_VARUSTE
INFRAO_LIIKENNEMERKKI_TAGS |= {
    "TEKSTI": [CORE_NS + ":teksti", "teksti"],
    "LIIKENNEMERKKITYYPPI": [CORE_NS + ":liikennemerkkityyppi", "cid_liikennemerkkityyppi"],
    "LIIKENNEMERKKITYYPPI2020": [CORE_NS + ":liikennemerkkityyppi2020", "cid_liikennemerkkityyppi2020"],
}


# infrao:Liikunta unique tags > inherit abstractpaikkatietopalvelukohde and abstractvaruste
INFRAO_LIIKUNTA_TAGS = {}
INFRAO_LIIKUNTA_TAGS |= INFRAO_ABSTRACT_PAIKKATIETOPALVELUKOHDE
INFRAO_LIIKUNTA_TAGS |= INFRAO_ABSTRACT_VARUSTE
INFRAO_LIIKUNTA_TAGS |= {
    "LIIKUNTA": [CORE_NS + ":liikunta", "cid_liikuntatyyppi"]
}

# infrao:Liite unique tags
INFRAO_LIITE_TAGS = {#TODO: remove if not needed
    "kuvaus": CORE_NS + ":kuvaus_liite",
    "linkkiliitteeseen": CORE_NS + ":linkkiliitteeseen_liite",
    "muokkaushetki": CORE_NS + ":muokkausHetki_liite",
    "versionumero": CORE_NS + ":versionumero_liite",
}

# infrao:Melu unique tags -> inherit abstractpaikkatietopalvelukohde and abstractvaruste
INFRAO_MELU_TAGS = {}
INFRAO_MELU_TAGS |= INFRAO_ABSTRACT_PAIKKATIETOPALVELUKOHDE
INFRAO_MELU_TAGS |= INFRAO_ABSTRACT_VARUSTE
INFRAO_MELU_TAGS |= {
    "MELU": [CORE_NS + ":melu", "cid_melutyyppi"]
}


# infrao:MuuKasvi unique tags -> inherit abstractpaikkatietopalvelukohde and abstractkasvillisuus
INFRAO_MUUKASVI_TAGS = {}
INFRAO_MUUKASVI_TAGS |= INFRAO_ABSTRACT_PAIKKATIETOPALVELUKOHDE
INFRAO_MUUKASVI_TAGS |= INFRAO_ABSTRACT_KASVILLISUUS
INFRAO_MUUKASVI_TAGS |= {
    "KASVIRYHMA": [CORE_NS + ":kasviryhma", "cid_kasviryhmatyyppi"],
    "KASVILAJI": [CORE_NS + ":kasvilaji", "cid_kasvilaji"]

}


# infrao:MuuVaruste unique tags -> inherit abstractpaikkatietopalvelukohde and abstractvaruste
INFRAO_MUUVARUSTE_TAGS = {}
INFRAO_MUUVARUSTE_TAGS |= INFRAO_ABSTRACT_PAIKKATIETOPALVELUKOHDE
INFRAO_MUUVARUSTE_TAGS |= INFRAO_ABSTRACT_VARUSTE
INFRAO_MUUVARUSTE_TAGS |= {
    "VARUSTETYYPPI": [CORE_NS + ":varustetyyppi", "cid_muuvarustetyyppi"]
}


# infrao:Nimi unique tags
INFRAO_NIMI_TAGS = {#TODO: remove if not needed
    "TEKSTI": [CORE_NS + ":teksti"]
}

# infrao:Opaste unique tags -> inherit abstractpaikkatietopalvelukohde and abstractvaruste

INFRAO_OPASTE_TAGS = {}

INFRAO_OPASTE_TAGS |= INFRAO_ABSTRACT_PAIKKATIETOPALVELUKOHDE
INFRAO_OPASTE_TAGS |= INFRAO_ABSTRACT_VARUSTE
INFRAO_OPASTE_TAGS |= {
    "OPASTE": [CORE_NS + ":opaste", "cid_opastetyyppi"]
}

# infrao:Osoite unique tags
INFRAO_OSOITE_TAGS = { #TODO: remove if not needed
    "kunta": CORE_NS + ":kunta",
    "osoitenumero": CORE_NS + ":osoitenumero",
    "osoitenumero2": CORE_NS + ":osoitenumero2",
    "jakokirjain": CORE_NS + ":jakokirjain",
    "jakokirjain2": CORE_NS + ":jakokirjain2",
    "porras": CORE_NS + ":porras",
    "huoneisto": CORE_NS + ":huoneisto",
    "huoneistojakokirjain": CORE_NS + ":huoneistojakokirjain",
    "postinumero": CORE_NS + ":postinumero",
    "postitoimipaikannimi": CORE_NS + ":postitoimipaikannimi",
    "geom_point": CORE_NS + ":pistesijainti",
    "geom_poly": CORE_NS + ":aluesijainti",
    "geom_line": CORE_NS + ":viivasijainti",
    "viitesijaintialue": CORE_NS + ":viitesijaintialue",
    "nimitieto": CORE_NS + ":nimitieto"
}

# infrao:Paatos unique tags
INFRAO_PAATOS_TAGS = { #TODO: remove if not needed
    #"LIITETIETO": [CORE_NS + ":liitetieto"],
    "paatos_kuvaus": CORE_NS + ":kuvaus",
    "paatos_paivamaarapvm": CORE_NS + ":paivamaaraPvm",
}

# infrao:Puu unique tags -> inherit abstractpaikkatietopalvelukohde and abstractkasvillisuus
INFRAO_PUU_TAGS = {}
INFRAO_PUU_TAGS |= INFRAO_ABSTRACT_PAIKKATIETOPALVELUKOHDE
INFRAO_PUU_TAGS |= INFRAO_ABSTRACT_KASVILLISUUS
INFRAO_PUU_TAGS |= {
    "KORKEUSMITTA": [CORE_NS + ":korkeusMitta", "korkeus"],
    "YMPARYSMITTA": [CORE_NS + ":ymparysMitta", "ymparys"],
    "PUUTYYPPI": [CORE_NS + ":puutyyppi", "cid_puutyyppi"],
    "PUULAJI": [CORE_NS + ":puulaji", "cid_puulaji"]
}


# infrao:Pysakointiruutu unique tags -> inherit abstractpaikkatietopalvelukohde and abstractvaruste
INFRAO_PYSAKOINTIRUUTU_TAGS = {}
INFRAO_PYSAKOINTIRUUTU_TAGS |= INFRAO_ABSTRACT_PAIKKATIETOPALVELUKOHDE
INFRAO_PYSAKOINTIRUUTU_TAGS |= INFRAO_ABSTRACT_VARUSTE
INFRAO_PYSAKOINTIRUUTU_TAGS |= {
    "LATAUSPISTEKYTKIN": [CORE_NS + ":latauspisteKytkin", "latauspiste_kytkin"]
}

# infrao:Rakenne unique tags -> inherit abstractpaikkatietopalvelukohde and abstractvaruste
INFRAO_RAKENNE_TAGS = {}
INFRAO_RAKENNE_TAGS |= INFRAO_ABSTRACT_PAIKKATIETOPALVELUKOHDE
INFRAO_RAKENNE_TAGS |= INFRAO_ABSTRACT_VARUSTE
INFRAO_RAKENNE_TAGS |= {
    "RAKENNE": [CORE_NS + ":rakenne", "cid_rakennetyyppi"]
}

# infrao:Sijainti unique tags
INFRAO_SIJAINTI_TAGS = { #TODO: remove if not needed
    "ALUE": [CORE_NS + ":alue"],
    "PISTE": [CORE_NS + ":piste"],
    "TYHJAGEOMETRIA": [CORE_NS + ":tyhjaGeometria"],
    "VIIVA": [CORE_NS + ":viiva"],
    "LUONTITAPA": [CORE_NS + ":luontitapa"],
    "OSOITETIETO": [CORE_NS + ":osoitetieto"],
    "SIJAINTIEPAVARMUUS": [CORE_NS + ":sijaintiepavarmuus"]
}

# infrao:Suunnitelmalinkki unique tags
INFRAO_SUUNNITELMALINKKI_TAGS = { #TODO: remove if not needed
    "suunnitelmakohdeid": CORE_NS + ":suunnitelmakohdeId",
}
INFRAO_SUUNNITELMALINKKI_TAGS |= INFRAO_LIITE_TAGS

# infrao:Viheralue unique tags -> inherit abstract paikkatietopalvelukohde

INFRAO_VIHERALUE_TAGS = {}
INFRAO_VIHERALUE_TAGS |= INFRAO_ABSTRACT_PAIKKATIETOPALVELUKOHDE
INFRAO_VIHERALUE_TAGS |= {
    "SISALTAAVIHERALUEENOSAN": [CORE_NS + ":sisaltaaViheralueenOsan", "skip"],
    "NIMI": [CORE_NS + ":nimi", "nimi"]
}


# infrao:ViheralueenOsa unique tags -> inherit abstract paikkatietopalvelukohde
INFRAO_VIHERALUEENOSA_TAGS = {}
INFRAO_VIHERALUEENOSA_TAGS |= INFRAO_ABSTRACT_PAIKKATIETOPALVELUKOHDE
INFRAO_VIHERALUEENOSA_TAGS |= {
    "OMISTAJA": [CORE_NS + ":omistaja", "omistaja"],
    "HALTIJA": [CORE_NS + ":haltija", "haltija"],
    "KUNNOSSAPITAJA": [CORE_NS + ":kunnossapitaja", "kunnossapitaja"],
    "PERUSPARANNUSVUOSI": [CORE_NS + ":perusparannusvuosi", "perusparannusvuosi"],
    "VALMISTUMISVUOSI": [CORE_NS + ":valmistumisvuosi", "valmistumisvuosi"],
    "SUOJELUALUEKYTKIN": [CORE_NS + ":suojelualuekytkin", "suojelualuekytkin"],
    "KUULUUVIHERALUEESEEN": [CORE_NS + ":kuuluuViheralueeseen", "fid_viheralue"],
    "KAYTTOTARKOITUS": [CORE_NS + ":kayttotarkoitus", "cid_viheralueenkayttotarkoitus"],
    "LAJI": [CORE_NS + ":laji", "cid_viherosanlajityyppi"],
    "HOITOLUOKKA": [CORE_NS + ":hoitoluokka", "cid_hoitoluokkatyyppi"],
    "SIJAINTITIETO": [CORE_NS + ":sijaintitieto", "geom"],
    "KATUALUEENLAJI": [CORE_NS + ":katualueenLaji", "cid_katuosanlaji"],
    "SUUNNITELMALINKKITIETO": [CORE_NS + ":suunnitelmalinkkitieto", "skip"],
    "TALVIHOIDONLUOKKA": [CORE_NS + ":talvihoidonLuokka", "cid_talvihoidonluokka"],
    "PUHTAANAPITOLUOKKA": [CORE_NS + ":puhtaanapitoluokka", "cid_puhtaanapitoluokkatyyppi"],
    "MUUTOSHOITOLUOKKA": [CORE_NS + ":muutoshoitoluokka", "cid_muutoshoitoluokkatyyppi"],
    "SISALTAAKASVILLISUUS": [CORE_NS + ":sisaltaaKasvillisuus", "skip"],
    "SISALTAAVARUSTE": [CORE_NS + ":sisaltaaVaruste", "skip"],
    "LUONTITAPA": [CORE_NS + ":luontitapa", "cid_luontitapatyyppi"],
    "OSOITE": [CORE_NS + ":osoitetieto", "fid_osoite"],
    "SIJAINTIEPAVARMUUS": [CORE_NS + ":sijaintiepavarmuus", "cid_sijaintiepavarmuustyyppi"],
}


# infrao:Ymparistotaide unique tags -> inherit abstractpaikkatietopalvelukohde and abstractvaruste
INFRAO_YMPARISTOTAIDE_TAGS = {}
INFRAO_YMPARISTOTAIDE_TAGS |= INFRAO_ABSTRACT_PAIKKATIETOPALVELUKOHDE
INFRAO_YMPARISTOTAIDE_TAGS |= INFRAO_ABSTRACT_VARUSTE
INFRAO_YMPARISTOTAIDE_TAGS |= {
    "YMPARISTOTAIDE": [CORE_NS + ":ymparistotaide", "cid_ymparistotaidetyyppi"]
}

# GML tags
GML_POINT = "gml:Point"
GML_LINESTRING = "gml:LineString"
GML_POLYGON = "gml:Polygon"
GML_EXTERIOR = "gml:exterior"
GML_INTERIOR = "gml:interior"
GML_LINEAR_RING = "gml:LinearRing"
GML_POS = "gml:pos"
GML_POS_LIST = "gml:posList"
GML_NULL = "gml:Null"
GML_ID = "gml:id"
GML_FEATURE_MEMBERS = "gml:featureMembers"
TIME_INSTANT = "gml:TimeInstant"
TIME_POSITION = "gml:timePosition"
TIME_PERIOD = "gml:TimePeriod"
BEGIN_POSITION = "gml:beginPosition"
END_POSITION = "gml:endPosition"
REFERENCE_IDENTIFIER = "gml:identifier"


TABLE_NAMES = [ #TODO: add other tables
    ("varusteet","jate"),
    ("varusteet","kaluste"),
    ("varusteet","leikkivaline"),
    ("varusteet","liikennemerkki"),
    ("varusteet","liikunta"),
    ("varusteet","melukohde"),
    ("varusteet","muuvaruste"),
    ("varusteet","opaste"),
    ("kasvillisuus","puu"),
    ("kasvillisuus","muukasvi"),
    ("kohteet","hulevesi"),
    ("kohteet","pysakointiruutu"),
    ("kohteet","rakenne"),
    ("kohteet","ymparistotaide"),
    ("katualue","ajoratamerkinta"),
    ("katualue","keskilinja"),
    ]

ELEMENT_NAMES = { #translate table name -> element name TODO: CHECK the element names, add others
    "jate": "Jate",
    "kaluste": "Kaluste",
    "leikkivaline": "Leikkivaline",
    "liikennemerkki": "Liikennemerkki",
    "liikunta": "Liikunta",
    "melukohde": "Melu",
    "muuvaruste": "MuuVaruste",
    "opaste": "Opaste",
    "viheralueenosa": "ViheralueenOsa",
    "katualueenosa": "KatualueenOsa",
    "viheralue": "Viheralue",
    "katualue": "Katualue",
    "puu": "Puu",
    "erikoisrakennekerros": "ErikoisrakenneKerros",
    "hulevesi": "Hulevesi",
    "kaluste" : "Kaluste",
    "keskilinja": "Keskilinja",
    "pysakointiruutu": "Pysakointiruutu",
    "rakenne": "Rakenne",
    "ymparistotaide": "Ymparistotaide",
    "muukasvi": "MuuKasvi",
    "ajoratamerkinta": "Ajoratamerkinta",
}

##Translate schema.table names -> tag dictionaries
SCHEMA_TABLE_NAMES = { #TODO: change order -> areas last?
    ("varusteet","jate"): INFRAO_JATE_TAGS,
    ("varusteet","kaluste"): INFRAO_KALUSTE_TAGS,
    ("varusteet","leikkivaline"): INFRAO_LEIKKIVALINE_TAGS,
    ("varusteet","liikunta"): INFRAO_LIIKUNTA_TAGS,
    ("varusteet","melukohde"): INFRAO_MELU_TAGS,
    ("varusteet","muuvaruste"): INFRAO_MUUVARUSTE_TAGS,
    ("varusteet","opaste"): INFRAO_OPASTE_TAGS,
    ("varusteet", "liikennemerkki"): INFRAO_LIIKENNEMERKKI_TAGS,
    ("viheralue", "viheralueenosa"): INFRAO_VIHERALUEENOSA_TAGS,
    ("viheralue", "viheralue"): INFRAO_VIHERALUE_TAGS,
    ("katualue", "katualue"): INFRAO_KATUALUE_TAGS,
    ("katualue", "katualueenosa"): INFRAO_KATUALUEENOSA_TAGS,
    ("katualue", "keskilinja"): INFRAO_KESKILINJA_TAGS,
    ("katualue", "ajoratamerkinta"): INFRAO_AJORATAMERKINTA_TAGS,
    ("kasvillisuus", "puu"): INFRAO_PUU_TAGS,
    ("kasvillisuus", "muukasvi"): INFRAO_MUUKASVI_TAGS,
    ("kohteet", "erikoisrakennekerros"): INFRAO_ERIKOISRAKENNEKERROS_TAGS,
    ("kohteet", "hulevesi"): INFRAO_HULEVESI_TAGS,
    ("kohteet", "pysakointiruutu"): INFRAO_PYSAKOINTIRUUTU_TAGS,
    ("kohteet", "rakenne"): INFRAO_RAKENNE_TAGS,
    ("kohteet", "ymparistotaide"): INFRAO_YMPARISTOTAIDE_TAGS,
}

AREA_NAMES = {
    "viheralueenosa": INFRAO_ABSTRACT_VARUSTE["KUULUUVIHERALUEENOSAAN"][0],
    "katualueenosa": INFRAO_ABSTRACT_VARUSTE["KUULUUKATUALUEENOSAAN"][0],
    "katualue": INFRAO_KATUALUEENOSA_TAGS["KUULUUKATUALUEESEEN"][0],
    "viheralue": INFRAO_VIHERALUEENOSA_TAGS["KUULUUVIHERALUEESEEN"][0],
}

AREA_INCLUDED_NAMES = {
    "viheralueenosa": [INFRAO_VIHERALUEENOSA_TAGS["SISALTAAVARUSTE"][0], INFRAO_VIHERALUEENOSA_TAGS["SISALTAAKASVILLISUUS"][0]],
    "katualueenosa": [INFRAO_KATUALUEENOSA_TAGS["SISALTAAVARUSTE"][0], INFRAO_KATUALUEENOSA_TAGS["SISALTAAKASVILLISUUS"][0], INFRAO_KATUALUEENOSA_TAGS["SISALTAAKESKILINJA"][0]],
    "katualue": [INFRAO_KATUALUE_TAGS["SISALTAAKATUALUEENOSAN"][0]],
    "viheralue": [INFRAO_VIHERALUE_TAGS["SISALTAAVIHERALUEENOSAN"][0]],
}

INFRAO_DIFF_SIJAINTI_TAGS = {
    "infrao:tarkkaSijaintitieto": "TARKKASIJAINTITIETO",
    "infrao:sijainti": "SIJAINTI",
    "infrao:sijaintitieto": "SIJAINTITIETO",
}

LOCATION_TAGS = ["infrao:tarkkaSijaintitieto", "infrao:sijainti", "infrao:sijaintitieto"]

PLAN_LINK_TABLES = [
    "ajoratamerkinta",
    "hulevesi",
    "jate",
    "kaluste",
    "leikkivaline",
    "liikennemerkki",
    "liikunta",
    "melukohde",
    "muuvaruste",
    "opaste",
    "pysakointiruutu",
    "rakenne",
    "ymparistotaide",
    "katualueenosa",
    "viheralueenosa",
]

LOGGER = logging.getLogger(plugin_name())

def get_decree_attachments(conn_params):
    """
    Fetches and attaches decrees (päätös) and their attachments (liite) to the corresponding part of street area (katualueenosa).

    Returns a dictionary where the fids of katalueenosa features are the keys and the value is a list of lists. The number of outer lists corresponds to the number of decrees the feature has. The inner lists contain dictionaries with the decree (paatos) and attachment (liite) values. The first dictionary is always the decree information.

    Args:
        conn_params (dict): Connection parameters to the postgis database.

    Returns:
        Dict: A dictionary where the fids of katualueenosa feature are keys and the decree and their attachment information are the values as lists of dictionaries.s
    """
    with(psycopg2.connect(**conn_params)) as conn:
        with conn.cursor(cursor_factory=DictCursor) as curs:
            attachment_query = SQL('SELECT {liite_kuvaus} AS liite_kuvaus, {liite_linkkiliitteeseen} AS liite_linkkiliitteeseen, {liite_muokkaushetki} AS liite_muokkaushetki, {liite_versionumero} AS liite_versionumero, {liite_id_paatos} AS liite_id_paatos FROM {liite_table};').format(
                liite_kuvaus=Identifier('kuvaus'),
                liite_linkkiliitteeseen=Identifier('linkkiliitteeseen'),
                liite_muokkaushetki=Identifier('muokkaushetki'),
                liite_versionumero=Identifier('versionumero'),
                liite_id_paatos=Identifier('id_paatos'),
                liite_table=Identifier('linkit', 'liite')
            )           
            decree_query = SQL('SELECT {paatos_id} AS paatos_id, {paatos_kuvaus} AS paatos_kuvaus, {paatos_paivamaarapvm} AS paatos_paivamaarapvm, {paatos_fid_katualueenosa} AS paatos_fid_katualueenosa FROM {paatos_table};').format(
                paatos_id=Identifier('id'),
                paatos_kuvaus=Identifier('kuvaus'),
                paatos_paivamaarapvm=Identifier('paivamaarapvm'),
                paatos_fid_katualueenosa=Identifier('fid_katualueenosa'),
                paatos_table=Identifier('linkit', 'paatos')
            )           
            curs.execute(attachment_query)
            attachment_results = curs.fetchall()
            attachment_columns = [desc[0] for desc in curs.description]
            curs.execute(decree_query)
            decree_results = curs.fetchall()

            attachment_dicts = {}

            for row in attachment_results:
                key = row[-1]
                if key not in attachment_dicts:
                    attachment_dicts[key] = []
                
                attachment_values = {attachment_columns[i]: row[i] for i in range(len(attachment_columns))}
                del attachment_values['liite_id_paatos']
                attachment_dicts[key].append(attachment_values)

            decree_dicts = []

            for row in decree_results:
                row_dict = [dict(row)]
                attachments = attachment_dicts.get(row_dict[0]['paatos_id'])

                del row_dict[0]['paatos_id']

                if attachments:
                    row_dict.extend(attachments)
                decree_dicts.append(row_dict)

            decree_attachments = {}

            for row in decree_dicts:
                key = row[0]['paatos_fid_katualueenosa']

                del row[0]['paatos_fid_katualueenosa']

                if key not in decree_attachments:
                    decree_attachments[key] = [row]
                else:
                    decree_attachments[key].append(row)
    return decree_attachments


def get_plan_link(conn_params):
    """
    Fetches all the plan link infromation (suunnitelmalinkkitieto) features and matches them with the features they belong to.

    Args:
        conn_params (dict): Connection parameters to the postgis database.

    Returns:
        dict: Table names are the keys. Value is a list of dictionaries with the suunnitelmalinkkitieto feature data.
    """
    plan_links_dict = {}
    for table in PLAN_LINK_TABLES:
        plan_links_dict[table] = {}
        with(psycopg2.connect(**conn_params)) as conn:
            with conn.cursor(cursor_factory=DictCursor) as curs:
                query = SQL('''SELECT {sl_alias}.{suunnitelmakohdeid},
                    {sl_alias}.{fid_table},
                    {l_alias}.{kuvaus},
                    {l_alias}.{linkkiliitteeseen},
                    {l_alias}.{muokkaushetki},
                    {l_alias}.{versionumero}
                    FROM {linkit}.{suunnitelmalinkki} AS {sl_alias}
                    JOIN {linkit}.{liite} AS {l_alias} ON {sl_alias}.{fid_liite} = {l_alias}.{fid}''').format(
                        sl_alias=Identifier("slinkki"),
                        suunnitelmakohdeid=Identifier("suunnitelmakohdeid"),
                        fid_table=Identifier(f"fid_{table}"),
                        l_alias=Identifier("l"),
                        kuvaus=Identifier("kuvaus"),
                        linkkiliitteeseen=Identifier("linkkiliitteeseen"),
                        muokkaushetki=Identifier("muokkaushetki"),
                        versionumero=Identifier("versionumero"),
                        suunnitelmalinkki=Identifier("suunnitelmalinkki"),
                        linkit=Identifier("linkit"),
                        liite=Identifier("liite"),
                        fid_liite=Identifier("fid_liite"),
                        fid = Identifier("fid"))
                try:
                    curs.execute(query)
                    results = curs.fetchall()
                    results_dict = []
                    for row in results:
                        row_dict = dict(row)
                        if row_dict[f"fid_{table}"] is not None:
                            results_dict.append(dict(row))
                    plan_links_dict[table] = results_dict
                except:
                    pass
    return plan_links_dict


def get_area_identifiers(conn_params):
    """
    Fetches information about what area different features belong to.

    Args:
        conn_params (dict): Connection parameters to the postgis database.

    Returns:
        dict: Area table names are the keys. Values is a list of dictionaries where the identifier key has the id of the area the features belongs to, and the rest of the keys are the tables whose features can belong to the area. Those keys' values is a list of the features ids.
    """
    results_dicts = {"viheralueenosa": [],
                     "katualueenosa": [],
                     "viheralue": [],
                     "katualue": [],}
    with(psycopg2.connect(**conn_params)) as conn:
        with conn.cursor(cursor_factory=DictCursor) as curs:
            for key in results_dicts:
                if "osa" in key:
                    query = SQL("SELECT {}.{}, ").format(Identifier(key), Identifier("identifier"))
                    for i, (schema, table) in enumerate(TABLE_NAMES):
                        if key == "viheralueenosa" and table == "keskilinja":
                            continue
                        else:
                            add_to_query = SQL("(SELECT array_agg({}.{}) FROM {}.{} WHERE {}.{} = {}.{}) AS {}").format(Identifier(table), Identifier("identifier"), Identifier(schema), Identifier(table), Identifier(table), Identifier(f"fid_{key}"), Identifier(key), Identifier("fid"), Identifier(table))
                            if key == "viheralueenosa" and i != len(TABLE_NAMES) - 2:
                                add_to_query += SQL(", ")
                            elif key == "katualueenosa" and i != len(TABLE_NAMES) - 1:
                                add_to_query += SQL(", ")
                            else:
                                add_to_query += SQL(" FROM {}.{}").format(Identifier(key[:-5]), Identifier(key))
                            query +=add_to_query
                else:
                    query = SQL("SELECT {}.{}, (SELECT array_agg({}.{}) FROM {}.{} WHERE {}.{} = {}.{}) AS {} FROM {}.{}").format(Identifier(key), Identifier("identifier"), Identifier(f"{key}enosa"), Identifier("identifier"), Identifier(key), Identifier(f"{key}enosa"), Identifier(f"{key}enosa"), Identifier(f"fid_{key}"), Identifier(key), Identifier("fid"), Identifier(f"{key}enosa"), Identifier(key), Identifier(key))
                curs.execute(query)
                results = curs.fetchall()
                results_dict = []
                for row in results:
                    results_dict.append(dict(row))
                results_dicts[key] = results_dict
    return results_dicts


def get_table_values(schema, table, dict_tags, conn_params):
    columns = []
    cids = []
    for k, v in dict_tags.items():
        if v[1] == "skip":
            columns.append((SQL("0"), Identifier(k)))
        elif v[1].startswith("geom") or v[0] in LOCATION_TAGS:
            columns.append((SQL("ST_AsGML(3, {}, options=>4)").format(Identifier(v[1])), Identifier(k)))
        elif v[1].startswith("cid_"):
            columns.append((SQL("{}.{}").format(Identifier(v[1].removeprefix("cid_")), Identifier("selite")), Identifier(k)))
            cids.append(v[1])
        else:
            columns.append((Identifier(v[1]), Identifier(k)))
    values = []
    with(psycopg2.connect(**conn_params)) as conn:
        conn.autocommit = True
        with conn.cursor() as curs:
            select_columns = SQL(',').join(SQL("{} AS {}").format(col, alias) for col, alias in columns)
            query = SQL("SELECT {} from {}.{}").format(select_columns, Identifier(schema), Identifier(table))
            if cids != []:
                joins = SQL(' ').join(SQL( "INNER JOIN {}.{} ON {}.{} = {}.{}").format(Identifier("koodistot"), Identifier(cid.removeprefix("cid_")), Identifier(table), Identifier(cid), Identifier(cid.removeprefix("cid_")), Identifier("cid")) for cid in cids)
                query = query + joins
            curs.execute(query)
            results = curs.fetchall()
            field_names = [field[0].upper() for field in curs.description]
            for row in results:
                feature_values = {}
                for i, name in enumerate(field_names):
                    feature_values[name] = row[i]

                feature_values["METATIETO"] = not all(meta_value is None for meta_key, meta_value in feature_values.items() if meta_key.startswith('META_'))

                values.append(feature_values)
    return values


def add_address(c_sij, xml_tag, conn_params, schema, table, value):
    c_osoitetieto = ET.SubElement(c_sij, xml_tag)
    c_osoite = ET.SubElement(c_osoitetieto, INFRAO_OSOITE)
    with(psycopg2.connect(**conn_params)) as conn:
        conn.autocommit = True
        with conn.cursor(cursor_factory=DictCursor) as curs:
            query = SQL("""
                SELECT {kunta}, {osoitenumero}, {osoitenumero2}, {jakokirjain}, {jakokirjain2}, {porras}, {huoneisto}, {huoneistojakokirjain},
                    {postinumero}, {postitoimipaikannimi},
                    ST_AsGML(3, {osoite_alias}.{geom_point}, options=>4) AS geom_point,
                    ST_AsGML(3, {osoite_alias}.{geom_poly}, options=>4) AS geom_poly,
                    ST_AsGML(3, {osoite_alias}.{geom_line}, options=>4) AS geom_line,
                    {viitesijaintialue}, {nimitieto}
                FROM osoite.osoite AS {osoite_alias}
                JOIN {schema}.{table} AS tb ON tb.fid_osoite = {osoite_alias}.fid
                WHERE tb.fid_osoite = {param}
            """).format(
                kunta=Identifier('kunta'),
                osoite_alias=Identifier('os'),
                osoitenumero=Identifier('osoitenumero'),
                osoitenumero2=Identifier('osoitenumero2'),
                jakokirjain=Identifier('jakokirjain'),
                jakokirjain2=Identifier('jakokirjain2'),
                porras=Identifier('porras'),
                huoneisto=Identifier('huoneisto'),
                huoneistojakokirjain=Identifier('huoneistojakokirjain'),
                postinumero=Identifier('postinumero'),
                postitoimipaikannimi=Identifier('postitoimipaikannimi'),
                viitesijaintialue=Identifier('viitesijaintialue'),
                nimitieto=Identifier('nimitieto'),
                geom_point=Identifier('geom_point'),
                geom_poly=Identifier('geom_poly'),
                geom_line=Identifier('geom_line'),
                schema=Identifier(schema),
                table=Identifier(table),
                param=Placeholder()
            )
            parameter = [value]
            curs.execute(query, parameter)
            osoite_results = dict(curs.fetchone())
            for osoite_key, osoite_value in osoite_results.items():
                if osoite_value is not None:
                    if osoite_key != "nimitieto" and not osoite_key.startswith("geom_"):
                        c_osoite_element = ET.SubElement(c_osoite, INFRAO_OSOITE_TAGS[osoite_key])
                        c_osoite_element.text = str(osoite_value)
                    elif osoite_key == "nimitieto":
                        c_nimitieto = ET.SubElement(c_osoite, INFRAO_OSOITE_TAGS[osoite_key])
                        c_nimi = ET.SubElement(c_nimitieto, INFRAO_NIMI)
                        c_teksti = ET.SubElement(c_nimi, "infrao:teksti")
                        c_teksti.text = str(osoite_value)
                    elif osoite_key.startswith("geom_"):
                        raw_gml_string = osoite_value
                        ns = ' xmlns:gml="http://www.opengis.net/gml/3.2"'
                        ET.register_namespace("gml", "http://www.opengis.net/gml/3.2")
                        p = raw_gml_string.find('srs') - 1
                        raw_gml_string = raw_gml_string[:p] + ns + raw_gml_string[p:]
                        c_osoite_geom = ET.SubElement(c_osoite, INFRAO_OSOITE_TAGS[osoite_key])
                        c_osoite_geom_element = ET.fromstring(raw_gml_string)
                        c_osoite_geom.append(c_osoite_geom_element)


def add_elements(schema, table, dict_tags, gml_fm, result_dicts, conn_params, values, plan_links_dict, decree_attachments):
    for n, o in globals().items():
        if o is dict_tags:
            dict_name = n
            break
    base_element_name = dict_name[:-5]
    base_element = globals()[base_element_name]

    location_tag = next(((k_, v_[0]) for k_, v_ in dict_tags.items() if v_[0] in LOCATION_TAGS and not k_.startswith("GEOM_")), None)

    if table in PLAN_LINK_TABLES:
        table_plan_links = plan_links_dict[table]

    for i in range(len(values)):
        empty_geometry = False
        if base_element not in [INFRAO_KESKILINJA, INFRAO_KATUALUEENOSA, INFRAO_VIHERALUEENOSA]:
            if location_tag:
                empty_geometry = all(values[i].get(tag) is None for tag in ["GEOM_POINT", "GEOM_LINE", location_tag[0]])

        belonging_checked = False
        location_created = False

        gml_id = {GML_ID:f"{base_element.removeprefix('infrao:')}.{values[i]['YKSILOINTITIETO']}"}
        f = ET.SubElement(gml_fm, base_element, attrib=gml_id)

        if values[i]["METATIETO"]:
            io_metatieto = ET.SubElement(f, "infrao:metatieto")
            gml_metadataproperty = ET.SubElement(io_metatieto, "gml:metaDataProperty")
            gml_genericmetadata = ET.SubElement(gml_metadataproperty, "gml:GenericMetaData")
        
        for key in values[i]:
            xml_tag = dict_tags[key][0]
            if xml_tag in LOCATION_TAGS and empty_geometry == True and not location_created:
                location_created = True
                c_base = ET.SubElement(f, xml_tag)
                c_sij = ET.SubElement(c_base, INFRAO_SIJAINTI)
                c_empty = ET.SubElement(c_sij, "infrao:tyhjaGeometria")
                ET.SubElement(c_empty, GML_NULL)
            if values[i][key] != NULL and values[i][key] != "Tyhjä":
                if xml_tag in LOCATION_TAGS:
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
                        c_base = ET.SubElement(f, xml_tag)
                        c_sij = ET.SubElement(c_base, INFRAO_SIJAINTI)
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
                elif xml_tag == "infrao:osoitetieto":
                    add_address(c_sij, xml_tag, conn_params, schema, table, values[i][key])
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
                elif xml_tag == "infrao:suunnitelmalinkkitieto":
                    plan_links_values = [p for p in table_plan_links if p.get(f'fid_{table}') == values[i]["FID"]]

                    if plan_links_values:
                        for plan_link_values in plan_links_values:
                            attachment_created = False
                            c_plan_link_parent = ET.SubElement(f, xml_tag)
                            c_plan_link_base = ET.SubElement(c_plan_link_parent, "infrao:Suunnitelmalinkki")
                            
                            for plan_key, plan_value in plan_link_values.items():
                                if plan_key.startswith("fid"):
                                    continue
                                
                                tag = INFRAO_SUUNNITELMALINKKI_TAGS[plan_key]
                                
                                if not tag.endswith("_liite") and plan_value is not None:
                                    c_plan_link_element = ET.SubElement(c_plan_link_base, tag)
                                    c_plan_link_element.text = str(plan_value)
                                else:
                                    if not attachment_created:
                                        c_attachment_parent = ET.SubElement(c_plan_link_base, "infrao:liitetieto")
                                        c_attachment_base = ET.SubElement(c_attachment_parent, "infrao:Liite")
                                        attachment_created = True
                                        
                                    if plan_value is not None:
                                        tag_without_suffix = tag.removesuffix("_liite")
                                        c_attachment_element = ET.SubElement(c_attachment_base, tag_without_suffix)
                                        
                                        if not tag.startswith("infrao:muokkaus"):
                                            c_attachment_element.text = str(plan_value)
                                        else:
                                            xsdt_str = plan_value.strftime('%Y-%m-%dT%H:%M:%S')
                                            c_attachment_element.text = xsdt_str
                elif xml_tag == "infrao:paatostieto":
                    decrees_and_their_attachments = decree_attachments.get(values[i]["FID"])
                    if decrees_and_their_attachments:
                        for item in decrees_and_their_attachments:
                            decree_grandparent = ET.SubElement(f, xml_tag)
                            decree_parent = ET.SubElement(decree_grandparent, "infrao:Paatos")
                            if len(item) > 1:
                                for attachment in item[1:]:
                                    attachment_grandparent = ET.SubElement(decree_parent, "infrao:liitetieto")
                                    attachment_parent = ET.SubElement(attachment_grandparent, INFRAO_LIITE)
                                    for l_key, l_value in attachment.items():
                                        if l_value is not None:
                                            attachment_element = ET.SubElement(attachment_parent, INFRAO_LIITE_TAGS[l_key.removeprefix("liite_")].removesuffix("_liite"))
                                            if l_key == "liite_muokkaushetki":
                                                xsdt_str = l_value.strftime('%Y-%m-%dT%H:%M:%S')
                                                attachment_element.text = xsdt_str
                                            else:
                                                attachment_element.text = str(l_value)

                            for p_key, p_value in item[0].items():
                                if p_value is not None:
                                    decree_element = ET.SubElement(decree_parent, INFRAO_PAATOS_TAGS[p_key])
                                    decree_element.text = str(p_value)
                elif xml_tag == "":
                    pass
                elif xml_tag == "infrao:metatieto":
                    pass
                elif key.startswith("META_"):
                    if values[i]["METATIETO"]:
                        meta_element = ET.SubElement(gml_genericmetadata, xml_tag)
                        meta_element.text = str(values[i][key])
                elif xml_tag == "infrao:alkuHetki" or xml_tag == "infrao:loppuHetki":
                    c_base = ET.SubElement(f, xml_tag)
                    date_time = values[i][key]
                    xsdt_str = date_time.strftime('%Y-%m-%dT%H:%M:%S')
                    c_base.text = xsdt_str
                elif "kytkin" in xml_tag.lower():
                    c_base = ET.SubElement(f, xml_tag)
                    c_base.text = str(values[i][key]).lower()
                elif not xml_tag.startswith("infrao:kuuluu"):
                    c_base = ET.SubElement(f, xml_tag)
                    c_base.text = str(values[i][key])


def add_shipment_information(root, shipment_information, conn_params):
    shipment_information_grandparent = ET.SubElement(root, "infrao:toimituksentiedot")
    shipment_information_parent = ET.SubElement(shipment_information_grandparent, "infrao:Toimitus")

    for key, value in shipment_information.items():
        if value:
            shipment_information_element = ET.SubElement(shipment_information_parent, INFRAO_AINEISTOTOIMITUKSEN_TIEDOT[key])
            shipment_information_element.text = value

    shipment_information["viety"] = True

    with(psycopg2.connect(**conn_params)) as conn:
        conn.autocommit = True
        with conn.cursor(cursor_factory=DictCursor) as curs:
            query = SQL('INSERT INTO {}.{} ({}) VALUES ({})').format(
                        Identifier("meta"),
                        Identifier("aineistotoimituksentiedot"),
                        SQL(', ').join(map(Identifier, shipment_information.keys())),
                        SQL(', ').join(Placeholder() * len(shipment_information.keys()))
            )                          
            curs.execute(query, list(shipment_information.values()))
            
    
    


def xml_export(conn_params, save_file, shipment_information):
    start = time.time()
    LOGGER.info("========================================XML EXPORT STARTED========================================")
    NAMESPACES = {
        "xmlns:infrao": 'www.infra-o.fi/infrao',
        "xsi:schemaLocation": 'www.infra-o.fi/infrao http://www.paikkatietopalvelu.fi/gml/infrao/2.0.2/infrao.xsd',
        "xmlns:xsi":"http://www.w3.org/2001/XMLSchema-instance",
        "xmlns:xlink":"http://www.w3.org/1999/xlink",
        }
    
    plan_links_dict = get_plan_link(conn_params)
    decree_attachments = get_decree_attachments(conn_params)
    result_dicts = get_area_identifiers(conn_params)
    root = ET.Element('infrao:InfraoKohteet',  NAMESPACES)
    gml_fm = ET.SubElement(root, GML_FEATURE_MEMBERS)

    for key, value in SCHEMA_TABLE_NAMES.items():
        try:
            table_values = get_table_values(key[0], key[1], value, conn_params)
            #get_table_values(schema, table, dict_tags, conn_params)
            if not table_values == []:
                add_elements(key[0], key[1], value, gml_fm, result_dicts, conn_params, table_values, plan_links_dict, decree_attachments)
        except Exception as e:
            LOGGER.info(f"Ongelma taulun {key[1]} viemisessä.")
            iface.messageBar().pushMessage(f"Ongelma taulun {key[1]} viemisessä.", level=1, duration=10)
            LOGGER.error(f"{e}")
            LOGGER.info(traceback.format_exc())
    
    if shipment_information:
        add_shipment_information(root, shipment_information, conn_params)

    tree = ET.ElementTree(root)
    ET.indent(tree, space="\t", level=0)
    tree.write(save_file, xml_declaration=True, encoding="utf-8")
    
    end = time.time()
    LOGGER.info("========================================XML EXPORT ENDED========================================")
    LOGGER.info(f"TIME ELAPSED: {round(((end-start) * 10**3)/1000, 2)} seconds.")