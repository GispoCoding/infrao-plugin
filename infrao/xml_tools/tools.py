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
import xml.etree.ElementTree as ET

CORE_NS = "infrao"

# infrao element tags
INFRAO_KOHTEET = CORE_NS + ":InfraoKohteet"
INFRAO_AJORATAMERKINTA = CORE_NS + ":Ajoratamerkinta"
INFRAO_ERIKOISRAKENNEKERROS = CORE_NS + ":ErikoisrakenneKerros"
INFRAO_HULEVESI = CORE_NS + ":Hulevesi"
INFRAO_JATE = CORE_NS + ":Jate"
INFRAO_KALUSTE = CORE_NS + ":Kaluste"
INFRAO_KATUALUE = CORE_NS + ":Katualue"
INFRAO_KATUALUEENOSA = CORE_NS + ":KatuAlueenOsa"
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


# infrao area element list
INFRAO_AREA_ELEMENTS = [
        INFRAO_KATUALUE,
        INFRAO_VIHERALUE,
        INFRAO_VIHERALUEENOSA,
        INFRAO_KATUALUEENOSA]

# infrao abstractpaikkatietopalvelukohde tags
INFRAO_ABSTRACT_PAIKKATIETOPALVELUKOHDE = {
    "FID": ["", "fid"],
    "METATIETO": [CORE_NS + ":metatieto", "metatieto"],
    "YKSILOINTITIETO": [CORE_NS + ":yksilointitieto", "identifier"],
    "ALKUHETKI": [CORE_NS + ":alkuHetki", "alkuhetki"],
    "LOPPUHETKI": [CORE_NS + ":loppuHetki", "loppuhetki"]
}

# infrao abstractvaruste tags
INFRAO_ABSTRACT_VARUSTE = {
    "GEOM_POINT": ["", "geom_point"],
    "GEOM_LINE": ["", "geom_line"], 
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
    #"SUUNNITELMALINKKITIETO": [CORE_NS + ":suunnitelmalinkkitieto", "suunnitelmalinkkitieto_id"],#TODO: ADD LATER
    "KUULUUVIHERALUEENOSAAN": [CORE_NS + ":kuuluuViheralueenOsaan", "fid_viheralueenosa"],
    "KUULUUKATUALUEENOSAAN": [CORE_NS + ":kuuluuKatuAlueenOsaan", "fid_katualueenosa"],
    "SIJAINTIEPAVARMUUS": [CORE_NS + ":sijaintiepavarmuus", "cid_sijaintiepavarmuustyyppi"],
    "LUONTITAPA": [CORE_NS + ":luontitapa", "cid_luontitapatyyppi"],
}

# infrao abstractkasvillisuus tags
INFRAO_ABSTRACT_KASVILLISUUS = {
    "OMISTAJA": [CORE_NS + ":omistaja", "omistaja"],
    "HALTIJA": [CORE_NS + ":haltija", "haltija"],
    "KUNNOSSAPITAJA": [CORE_NS + ":kunnossapitaja", "kunnossapitaja"],
    "GEOM_POINT": ["", "geom_point"],
    "GEOM_LINE": ["", "geom_line"], 
    "SIJAINTITIETO": [CORE_NS + ":sijaintitieto", "geom_poly"],
    "KUULUUVIHERALUEENOSAAN": [CORE_NS + ":kuuluuViheralueenOsaan", "fid_viheralueenosa"],
    "KUULUUKATUALUEENOSAAN": [CORE_NS + ":kuuluuKatuAlueenOsaan", "fid_katualueenosa"],
    "SIJAINTIEPAVARMUUS": [CORE_NS + ":sijaintiepavarmuus", "cid_sijaintiepavarmuustyyppi"],
    "LUONTITAPA": [CORE_NS + ":luontitapa", "cid_luontitapatyyppi"],
}

## ELEMENT TAGS
# infrao:Ajoratamerkinta unique tags -> inherit abstractpaikkatietopalvelukohde and abstractvaruste
INFRAO_AJORATAMERKINTA_TAGS = {
    "JYRSITTYPINTAKYTKIN": [CORE_NS + ":jyrsittyPintaKytkin", "jyrsittypinta_kytkin"],
    "TYYPPI": [CORE_NS + ":tyyppi", "cid_ajoratamerkintatyyppi"]
}
INFRAO_AJORATAMERKINTA_TAGS |= INFRAO_ABSTRACT_PAIKKATIETOPALVELUKOHDE
INFRAO_AJORATAMERKINTA_TAGS |= INFRAO_ABSTRACT_VARUSTE

# infrao:ErikoisrakenneKerros -> inherit abstractpaikkatietopalvelukohde
INFRAO_ERIKOISRAKENNEKERROS_TAGS = {
    "OMISTAJA": [CORE_NS + ":omistaja", "omistaja"],
    "HALTIJA": [CORE_NS + ":haltija", "haltija"],
    "KUNNOSSAPITAJA": [CORE_NS + ":kunnossapitaja", "kunnossapitaja"],
    "SELITE": [CORE_NS + ":selite", "selite"],
    "MATERIAALI": [CORE_NS + ":materiaali", "materiaali"],
    "TYYPPI": [CORE_NS + ":tyyppi", "cid_erikoisrakennekerrosmateriaalityyppi"],
    "SIJAINTI": [CORE_NS + ":sijainti", "geom_poly"],
    "GEOM_POINT": ["", "geom_point"],
    "GEOM_LINE": ["", "geom_line"],
    "SIJAINTIEPAVARMUUS": [CORE_NS + ":sijaintiepavarmuus", "cid_sijaintiepavarmuustyyppi"],
    "LUONTITAPA": [CORE_NS + ":luontitapa", "cid_luontitapatyyppi"],
}
INFRAO_ERIKOISRAKENNEKERROS_TAGS |= INFRAO_ABSTRACT_PAIKKATIETOPALVELUKOHDE

# infrao:Hulevesi unique tags -> inherit abstractpaikkatietopalvelukohde and abstractvaruste
INFRAO_HULEVESI_TAGS = {
    "HULEVESI": [CORE_NS + ":hulevesi", "cid_hulevesityyppi"]
}
INFRAO_HULEVESI_TAGS |= INFRAO_ABSTRACT_PAIKKATIETOPALVELUKOHDE
INFRAO_HULEVESI_TAGS |= INFRAO_ABSTRACT_VARUSTE

# infrao:InfraoKohteet unique tags
INFRAO_INFRAOKOHTEET_TAGS = { #TODO: remove if not needed
    "TOIMITUKSENTIEDOT": [CORE_NS + ":toimituksentiedot"]
}

# infrao:Jate unique tags -> inherit abstractpaikkatietopalvelukohde and abstractvaruste
INFRAO_JATE_TAGS = {
    "KOKO": [CORE_NS + ":koko", "koko"],
    "PUTKIKERAYSJARJESTELMAKYTKIN": [CORE_NS + ":putkikeraysjarjestelmaKytkin", "putkikeraysjarjestelma_kytkin"],
    "SIJAINTIMAANPINNALLAKYTKIN": [CORE_NS + ":sijaintiMaanPinnallaKytkin", "sijaintimaanpinnalla_kytkin"],
    "VAARALLISTENJATEASTIAKYTKIN":[CORE_NS + ":vaarallistenJateastiaKytkin", "vaarallistenjateastia_kytkin"],
    "JATE": [CORE_NS + ":jate", "cid_jatetyyppi"]
}
INFRAO_JATE_TAGS |= INFRAO_ABSTRACT_PAIKKATIETOPALVELUKOHDE
INFRAO_JATE_TAGS |= INFRAO_ABSTRACT_VARUSTE

# infrao:Kaluste unique tags -> inherit abstractpaikkatietopalvelukohde and abstractvaruste
INFRAO_KALUSTE_TAGS = {
    "KALUSTE": [CORE_NS + ":kaluste", "cid_kalustetyyppi"]
}
INFRAO_KALUSTE_TAGS |= INFRAO_ABSTRACT_PAIKKATIETOPALVELUKOHDE
INFRAO_KALUSTE_TAGS |= INFRAO_ABSTRACT_VARUSTE

# infrao:Katualue unique tags -> inherit abstractpaikkatietopalvelukohde
INFRAO_KATUALUE_TAGS = {
    "SISALTAAKATUALUEENOSAN": [CORE_NS + ":sisaltaaKatualueenOsan", "sisaltaakatualueenosan"],
    "NIMI": [CORE_NS + ":nimi", "nimi"]
}
INFRAO_KATUALUE_TAGS |= INFRAO_ABSTRACT_PAIKKATIETOPALVELUKOHDE

# infrao:KatualueenOsa unique tags -> inherit abstractpaikkatietopalvelukohde
INFRAO_KATUALUEENOSA_TAGS = {
    #"PAATOSTIETO": [CORE_NS + ":paatostieto"], TODO: add later
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
    "SISALTAAKESKILINJA": [CORE_NS + ":sisaltaaKeskilinja", "sisaltaakeskilinja"],
    "LUOKKA": [CORE_NS + ":luokka", "luokka_id"],
    "LAJI": [CORE_NS + ":laji", "katuosanlaji_id"],
    "VIHERALUEENLAJI": [CORE_NS + ":viheralueenLaji", "viherosanlajityyppi_id"],
    "PINTAMATERIAALI": [CORE_NS + ":pintamateriaali", "pintamateriaali_id"],
    "KUNNOSSAPITOLUOKKA": [CORE_NS + ":kunnossapitoluokka", "kunnossapitoluokka_id"],
    "SIJAINTITIETO": [CORE_NS + ":sijaintitieto", "geom"], 
    #"SUUNNITELMALINKKITIETO": [CORE_NS + ":suunnitelmalinkkitieto", ""], #TODO: add later
    "TALVIHOIDONLUOKKA": [CORE_NS + ":talvihoidonLuokka", "talvihoidonluokka_id"],
    "SISALTAAKASVILLISUUS": [CORE_NS + ":sisaltaaKasvillisuus", "sisaltaakasvillisuus"],
    "SISALTAAVARUSTE": [CORE_NS + ":sisaltaaVaruste", "sisaltaavaruste"],
    "SIJAINTIEPAVARMUUS": [CORE_NS + ":sijaintiepavarmuus", "cid_sijaintiepavarmuustyyppi"],
    "LUONTITAPA": [CORE_NS + ":luontitapa", "cid_luontitapatyyppi"],
}
INFRAO_KATUALUEENOSA_TAGS |= INFRAO_ABSTRACT_PAIKKATIETOPALVELUKOHDE

# infrao:Keskilinja unique tags -> inherit abstractpaikkatietopalvelukohde
INFRAO_KESKILINJA_TAGS = {
    "DIGIROADID": [CORE_NS + ":DigiroadID", "digiroadid"],
    "SIJAINTI": [CORE_NS + ":sijainti", "geom"],
    "KUULUUKATUALUEENOSAAN": [CORE_NS + ":kuuluuKatualueenOsaan", "fid_katualueenosa"],
}
INFRAO_KESKILINJA_TAGS |= INFRAO_ABSTRACT_PAIKKATIETOPALVELUKOHDE

# infrao:Leikkivaline unique tags -> inherit abstractpaikkatietopalvelukohde and abstractvaruste
INFRAO_LEIKKIVALINE_TAGS = {
    "TOIMINNALLINENTARKASTUSPVM": [CORE_NS + ":toiminnallinenTarkastusPvm", "toiminnallinentarkastus_pvm"],
    "VUOSITARKASTUSPVM": [CORE_NS + ":vuositarkastusPvm", "vuositarkastus_pvm"],
    "LEIKKIVALINE": [CORE_NS + ":leikkivaline", "cid_leikkivalinetyyppi"]
}
INFRAO_LEIKKIVALINE_TAGS |= INFRAO_ABSTRACT_PAIKKATIETOPALVELUKOHDE
INFRAO_LEIKKIVALINE_TAGS |= INFRAO_ABSTRACT_VARUSTE

# infrao:Liikennemerkki tags -> inherit abstractpaikkatietopalvelukohde and abstractvaruste
INFRAO_LIIKENNEMERKKI_TAGS = {
    "TEKSTI": [CORE_NS + ":teksti", "teksti"],
    "LIIKENNEMERKKITYYPPI": [CORE_NS + ":liikennemerkkityyppi", "cid_liikennemerkkityyppi"],
    "LIIKENNEMERKKITYYPPI2020": [CORE_NS + ":liikennemerkkityyppi2020", "cid_liikennemerkkityyppi2020"]
}
INFRAO_LIIKENNEMERKKI_TAGS |= INFRAO_ABSTRACT_PAIKKATIETOPALVELUKOHDE
INFRAO_LIIKENNEMERKKI_TAGS |= INFRAO_ABSTRACT_VARUSTE

# infrao:Liikunta unique tags > inherit abstractpaikkatietopalvelukohde and abstractvaruste
INFRAO_LIIKUNTA_TAGS = {
    "LIIKUNTA": [CORE_NS + ":liikunta", "cid_liikuntatyyppi"]
}
INFRAO_LIIKUNTA_TAGS |= INFRAO_ABSTRACT_PAIKKATIETOPALVELUKOHDE
INFRAO_LIIKUNTA_TAGS |= INFRAO_ABSTRACT_VARUSTE

# infrao:Liite unique tags
INFRAO_LIITE_TAGS = {#TODO: remove if not needed
    "KUVAUS": [CORE_NS + ":kuvaus", "kuvaus"],
    "LINKKILIITTEESEEN": [CORE_NS + ":linkkiliitteeseen", "linkkiliitteeseen"],
    "MUOKKAUSHETKI": [CORE_NS + ":muokkausHetki", "muokkaushetki"],
    "VERSIONUMERO": [CORE_NS + ":versionumero", "versionumero"]
}

# infrao:Melu unique tags -> inherit abstractpaikkatietopalvelukohde and abstractvaruste
INFRAO_MELU_TAGS = {
    "MELU": [CORE_NS + ":melu", "cid_melutyyppi"]
}
INFRAO_MELU_TAGS |= INFRAO_ABSTRACT_PAIKKATIETOPALVELUKOHDE
INFRAO_MELU_TAGS |= INFRAO_ABSTRACT_VARUSTE

# infrao:MuuKasvi unique tags -> inherit abstractpaikkatietopalvelukohde and abstractkasvillisuus
INFRAO_MUUKASVI_TAGS = {
    "KASVIRYHMA": [CORE_NS + ":kasviryhma", "cid_kasviryhmatyyppi"],
    "KASVILAJI": [CORE_NS + ":kasvilaji", "cid_kasvilaji"]

}
INFRAO_MUUKASVI_TAGS |= INFRAO_ABSTRACT_PAIKKATIETOPALVELUKOHDE
INFRAO_MUUKASVI_TAGS |= INFRAO_ABSTRACT_KASVILLISUUS

# infrao:MuuVaruste unique tags -> inherit abstractpaikkatietopalvelukohde and abstractvaruste
INFRAO_MUUVARUSTE_TAGS = {
    "VARUSTETYYPPI": [CORE_NS + ":varustetyyppi", "cid_muuvarustetyyppi"]
}
INFRAO_MUUVARUSTE_TAGS |= INFRAO_ABSTRACT_PAIKKATIETOPALVELUKOHDE
INFRAO_MUUVARUSTE_TAGS |= INFRAO_ABSTRACT_VARUSTE

# infrao:Nimi unique tags
INFRAO_NIMI_TAGS = {#TODO: remove if not needed
    "TEKSTI": [CORE_NS + ":teksti"]
}

# infrao:Opaste unique tags -> inherit abstractpaikkatietopalvelukohde and abstractvaruste
INFRAO_OPASTE_TAGS = {
    "OPASTE": [CORE_NS + ":opaste", "cid_opastetyyppi"]
}
INFRAO_OPASTE_TAGS |= INFRAO_ABSTRACT_PAIKKATIETOPALVELUKOHDE
INFRAO_OPASTE_TAGS |= INFRAO_ABSTRACT_VARUSTE

# infrao:Osoite unique tags
INFRAO_OSOITE_TAGS = { #TODO: remove if not needed
    "KUNTA": [CORE_NS + ":kunta"],
    "OSOITENUMERO": [CORE_NS + ":osoitenumero"],
    "OSOITENUMERO2": [CORE_NS + ":osoitenumero2"],
    "JAKOKIRJAIN": [CORE_NS + ":jakokirjain"],
    "JAKOKIRJAIN2": [CORE_NS + ":jakokirjain2"],
    "PORRAS": [CORE_NS + ":porras"],
    "HUONEISTO": [CORE_NS + ":huoneisto"],
    "HUONEISTOJAKOKIRJAIN": [CORE_NS + ":huoneistojakokirjain"],
    "POSTINUMERO": [CORE_NS + ":postinumero"],
    "POSTITOIMIPAIKANNIMI": [CORE_NS + ":postitoimipaikannimi"],
    "PISTESIJAINTI": [CORE_NS + ":pistesijainti"],
    "ALUESIJAINTI": [CORE_NS + ":aluesijainti"],
    "VIIVASIJAINTI": [CORE_NS + ":viivasijainti"],
    "VIITESIJAINTIALUE": [CORE_NS + ":viitesijaintialue"],
    "NIMITIETO": [CORE_NS + ":nimitieto"]
}

# infrao:Paatos unique tags
INFRAO_PAATOS_TAGS = { #TODO: remove if not needed
    "LIITETIETO": [CORE_NS + ":liitetieto"],
    "KUVAUS": [CORE_NS + ":kuvaus"],
    "PAIVAMAARAPVM": [CORE_NS + ":paivamaaraPvm"]
}

# infrao:Puu unique tags -> inherit abstractpaikkatietopalvelukohde and abstractkasvillisuus
INFRAO_PUU_TAGS = {
    "KORKEUSMITTA": [CORE_NS + ":korkeusMitta", "korkeus"],
    "YMPARYSMITTA": [CORE_NS + ":ymparysMitta", "ymparys"],
    "PUUTYYPPI": [CORE_NS + ":puutyyppi", "cid_puutyyppi"],
    "PUULAJI": [CORE_NS + ":puulaji", "cid_puulaji"]
}
INFRAO_PUU_TAGS |= INFRAO_ABSTRACT_PAIKKATIETOPALVELUKOHDE
INFRAO_PUU_TAGS |= INFRAO_ABSTRACT_KASVILLISUUS

# infrao:Pysakointiruutu unique tags -> inherit abstractpaikkatietopalvelukohde and abstractvaruste
INFRAO_PYSAKOINTIRUUTU_TAGS = {
    "LATAUSPISTEKYTKIN": [CORE_NS + ":latauspisteKytkin", "latauspiste_kytkin"]
}
INFRAO_PYSAKOINTIRUUTU_TAGS |= INFRAO_ABSTRACT_PAIKKATIETOPALVELUKOHDE
INFRAO_PYSAKOINTIRUUTU_TAGS |= INFRAO_ABSTRACT_VARUSTE

# infrao:Rakenne unique tags -> inherit abstractpaikkatietopalvelukohde and abstractvaruste
INFRAO_RAKENNE_TAGS = {
    "RAKENNE": [CORE_NS + ":rakenne", "cid_rakennetyyppi"]
}
INFRAO_RAKENNE_TAGS |= INFRAO_ABSTRACT_PAIKKATIETOPALVELUKOHDE
INFRAO_RAKENNE_TAGS |= INFRAO_ABSTRACT_VARUSTE

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

# infrao:Suunnitelma unique tags
INFRAO_SUUNNITELMA_TAGS = { #TODO: remove if not needed
    "LIITETIETO": [CORE_NS + ":liitetieto"],
    "KUVAUS": [CORE_NS + ":kuvaus"],
    "PAIVAMAARAPVM": [CORE_NS + ":paivamaaraPvm"]
}

# infrao:Suunnitelmalinkki unique tags
INFRAO_SUUNNITELMALINKKI_TAGS = { #TODO: remove if not needed
    "SUUNNITELMAKOHDEID": [CORE_NS + ":SuunnitelmakohdeId"],
    "LIITETIETO": [CORE_NS + ":liitetieto"]
}

# infrao:Viheralue unique tags -> inherit abstract paikkatietopalvelukohde
INFRAO_VIHERALUE_TAGS = {
    "SISALTAAVIHERALUEENOSAN": [CORE_NS + ":sisaltaaViheralueeonOsan", "sisaltaaviheralueenosan"],
    "NIMI": [CORE_NS + ":nimi", "nimi"]
}
INFRAO_VIHERALUE_TAGS |= INFRAO_ABSTRACT_PAIKKATIETOPALVELUKOHDE

# infrao:ViheralueenOsa unique tags -> inherit abstract paikkatietopalvelukohde
INFRAO_VIHERALUEENOSA_TAGS = {
    "OMISTAJA": [CORE_NS + ":omistaja", "omistaja"],
    "HALTIJA": [CORE_NS + ":haltija", "haltija"],
    "KUNNOSSAPITAJA": [CORE_NS + ":kunnossapitaja", "kunnossapitaja"],
    "PERUSPARANNUSVUOSI": [CORE_NS + ":perusparannusvuosi", "perusparannusvuosi"],
    "VALMISTUMISVUOSI": [CORE_NS + ":valmistumisvuosi", "valmistumisvuosi"],
    "SUOJELUALUEKYTKIN": [CORE_NS + ":suojelualuekytkin", "suojelualuekytkin"],
    "KUULUUVIHERALUEESEEN": [CORE_NS + ":kuuluuViheralueeseen", "fid_viheralue"],
    "KAYTTOTARKOITUS": [CORE_NS + ":kayttotarkoitus", "kayttotarkoitus_id"],
    "LAJI": [CORE_NS + ":laji", "laji_id"],
    "HOITOLUOKKA": [CORE_NS + ":hoitoluokka", "hoitoluokka_id"],
    "SIJAINTITIETO": [CORE_NS + ":sijaintitieto", "geom"],
    "KATUALUEENLAJI": [CORE_NS + ":katualueenLaji", "katualueenlaji_id"],
    "SUUNNITELMALINKKITIETO": [CORE_NS + ":suunnitelmalinkkitieto", "suunnitelmalinkkitieto_id"],
    "TALVIHOIDONLUOKKA": [CORE_NS + ":talvihoidonLuokka", "talvihoidonluokka_id"],
    "PUHTAANAPITOLUOKKA": [CORE_NS + ":puhtaanapitoluokka", "puhtaanapitoluokka_id"],
    "MUUTOSHOITOLUOKKA": [CORE_NS + ":muutoshoitoluokka", "muutoshoitoluokka_id"],
    "SISALTAAKASVILLISUUS": [CORE_NS + ":sisaltaaKasvillisuus", "sisaltaakasvillisuus"],
    "SISALTAAVARUSTE": [CORE_NS + ":sisaltaaVaruste", "sisaltaavaruste"],
    "SIJAINTIEPAVARMUUS": [CORE_NS + ":sijaintiepavarmuus", "cid_sijaintiepavarmuustyyppi"],
    "LUONTITAPA": [CORE_NS + ":luontitapa", "cid_luontitapatyyppi"],
}
INFRAO_VIHERALUEENOSA_TAGS |= INFRAO_ABSTRACT_PAIKKATIETOPALVELUKOHDE

# infrao:Ymparistotaide unique tags -> inherit abstractpaikkatietopalvelukohde and abstractvaruste
INFRAO_YMPARISTOTAIDE_TAGS = {
    "YMPARISTOTAIDE": [CORE_NS + ":ymparistotaide", "cid_ymparistotaidetyyppi"]
}
INFRAO_YMPARISTOTAIDE_TAGS |= INFRAO_ABSTRACT_PAIKKATIETOPALVELUKOHDE
INFRAO_YMPARISTOTAIDE_TAGS |= INFRAO_ABSTRACT_VARUSTE

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
    "katualueenosa": "KatuAlueenOsa",
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