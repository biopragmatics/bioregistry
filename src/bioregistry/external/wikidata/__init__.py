"""Query, download, and format Wikidata as a registry."""

import json
import logging
from collections.abc import Iterable, Mapping
from pathlib import Path
from textwrap import dedent
from typing import Any

import wikidata_client

from bioregistry.alignment_model import Record, make_record
from bioregistry.constants import BIOREGISTRY_PATH, URI_FORMAT_KEY
from bioregistry.external.alignment_utils import Aligner, build_no_raw_getter
from bioregistry.utils import removeprefix

__all__ = [
    "WikidataAligner",
    "get_wikidata",
]

logger = logging.getLogger(__name__)

HERE = Path(__file__).parent.resolve()
PROCESSED_PATH = HERE / "processed.json"
CONFIG_PATH = HERE / "config.json"

PROPERTIES_QUERY = dedent(
    """\
    SELECT ?propStr
    WHERE {
      VALUES ?category {
        wd:Q21294996  # chemistry
        wd:Q22988603  # biology
        wd:Q80840868  # research
      }
      ?prop wdt:P31/wdt:P279+ ?category .
      BIND( SUBSTR(STR(?prop), 32) AS ?propStr )
    }
    ORDER BY ?prop
    """
)

#: A query to wikidata for properties related to chemistry, biology, and related
QUERY_FMT = dedent(
    """\
    SELECT DISTINCT
      (?prop AS ?prefix)
      ?propLabel
      ?propDescription
      ?miriam
      ?pattern
      (GROUP_CONCAT(DISTINCT ?homepage_; separator='\\t') AS ?homepage)
      (GROUP_CONCAT(DISTINCT ?format_; separator='\\t') AS ?uri_format)
      (GROUP_CONCAT(DISTINCT ?format_rdf_; separator='\\t') AS ?uri_format_rdf)
      (GROUP_CONCAT(DISTINCT ?database_; separator='\\t') AS ?database)
      (GROUP_CONCAT(DISTINCT ?examples_; separator='\\t') AS ?examples)
      (GROUP_CONCAT(DISTINCT ?short_name_; separator='\\t') AS ?short_names)
    WHERE {
      {
        VALUES ?category {
          wd:Q21294996  # chemistry
          wd:Q22988603  # biology
          wd:Q80840868  # research
        }
        ?prop wdt:P31/wdt:P279+ ?category .
      }
      UNION {
        VALUES ?prop { %s }
      }
      BIND( SUBSTR(STR(?prop), 32) AS ?propStr )
      OPTIONAL { ?prop wdt:P1793 ?pattern }
      OPTIONAL { ?prop wdt:P4793 ?miriam }

      OPTIONAL { ?prop wdt:P1813 ?short_name_ }
      OPTIONAL { ?prop wdt:P1896 ?homepage_ }
      OPTIONAL { ?prop wdt:P1630 ?format_ }
      OPTIONAL { ?prop wdt:P1921 ?format_rdf_ }
      OPTIONAL { ?prop wdt:P1629 ?database_ }
      OPTIONAL {
        ?prop p:P1855 ?statement .
        ?statement ?propQualifier ?examples_ .
        FILTER (STRSTARTS(STR(?propQualifier), "http://www.wikidata.org/prop/qualifier/"))
        FILTER (?propStr = SUBSTR(STR(?propQualifier), 40))
      }
      SERVICE wikibase:label { bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en". }
    }
    GROUP BY ?prop ?propLabel ?propDescription ?miriam ?pattern
    ORDER BY ?prop
    """
)

CONFIG = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
SKIP = CONFIG["skips"]

RENAMES = {"propLabel": "name", "propDescription": "description"}
CANONICAL_DATABASES = {
    "P6800": "Q87630124",  # -> NCBI Genome
    "P627": "Q48268",  # -> International Union for Conservation of Nature
    "P351": "Q1345229",  # NCBI Gene
    "P4168": "Q112783946",  # Immune epitope database
}

CANONICAL_HOMEPAGES: dict[str, str] = {
    "P6852": "https://www.ccdc.cam.ac.uk",
    "P7224": "http://insecta.pro/catalog",
    "P1761": "http://delta-intkey.com",
    "P2083": "http://www.leadscope.com",
    "P7965": "https://www.scilit.net",
    "P7963": "https://github.com/obophenotype/cell-ontology",
    "P2275": "http://www.who.int/medicines/services/inn/en/",
    "P10246": "https://medlineplus.gov/druginfo/herb_All.html",
    "P10245": "https://medlineplus.gov/druginfo/drug_Aa.html",
    "P9704": "https://www.monumentaltrees.com/en/",
    "P9356": "http://portal.hymao.org/projects/32/public/label/list_all",
    "P3088": "https://taibnet.sinica.edu.tw/home_eng.php",
    "P486": "http://www.nlm.nih.gov",
}
CANONICAL_URI_FORMATS = {
    "P830": "https://eol.org/pages/$1",
    "P2085": "https://jglobal.jst.go.jp/en/redirect?Nikkaji_No=$1",
    "P604": "https://medlineplus.gov/ency/article/$1.htm",
    "P492": "https://omim.org/OMIM:$1",
    "P486": "http://www.nlm.nih.gov",
    "P3201": "http://bioportal.bioontology.org/ontologies/MEDDRA?p=classes&conceptid=$1",
    "P7224": "http://insecta.pro/taxonomy/$1",
    "P3088": "https://taibnet.sinica.edu.tw/eng/taibnet_species_detail.php?name_code=$1",
    "P8150": "https://search.bvsalud.org/global-literature-on-novel-coronavirus-2019-ncov/resource/en/$1",
    "P9272": "https://decs.bvsalud.org/ths/resource/?id=$1",
    "P8082": "https://www.mscbs.gob.es/ciudadanos/centros.do?metodo=realizarDetalle&tipo=hospital&numero=$1",
    "P10095": "https://www.surgeons.org/Profile/$1",
    "P5397": "http://www.tierstimmen.org/en/database?field_spec_species_target_id_selective=$1",
    "P7471": "https://www.inaturalist.org/places/$1",
    "P696": "https://scicrunch.org/scicrunch/interlex/view/ilx_$1",
}
CANONICAL_RDF_URI_FORMATS: dict[str, str] = {}

# Stuff with miriam IDs that shouldn't

MIRIAM_BLACKLIST = {
    "Q106201090",
    "Q106201514",
    "Q106201904",
    "Q106201991",
    "Q106695243",
    "Q106832467",
    "Q47519952",
    "Q51162088",
    "Q56221155",
    "Q96212863",
}
URI_FORMAT_BLACKLIST = {
    ("P4229", "https://icdcodelookup.com/icd-10/codes/$1"),
    ("P696", "http://uri.neuinfo.org/nif/nifstd/$1"),
}


def _get_mapped() -> set[str]:
    return {
        value
        for record in json.loads(BIOREGISTRY_PATH.read_text()).values()
        for metaprefix, value in record.get("mappings", {}).items()
        if metaprefix == "wikidata"
    }


def _get_query(properties: Iterable[str]) -> str:
    values = " ".join(f"wd:{p}" for p in properties)
    return QUERY_FMT % values


def _get_wikidata() -> dict[str, Record]:
    """Iterate over Wikidata properties connected to biological databases."""
    mapped = _get_mapped()
    # throw out anything that can be queried directly
    mapped.difference_update(
        bindings["propStr"]
        for bindings in wikidata_client.query(PROPERTIES_QUERY)
        if bindings["propStr"].startswith("P")  # throw away any regular ones
    )
    raw_records = wikidata_client.query(_get_query(mapped))

    rv = {}
    for raw_record in raw_records:
        prefix, record = _process_record(raw_record)
        if prefix and record:
            rv[prefix] = record
    return rv


def _process_record(bindings: Mapping[str, Any]) -> tuple[str, Record] | tuple[None, None]:
    bindings = {RENAMES.get(key, key): value for key, value in bindings.items() if value}
    prefix = bindings["prefix"] = removeprefix(
        bindings["prefix"], "http://www.wikidata.org/entity/"
    )
    if prefix in SKIP or not prefix:
        return None, None

    examples = bindings.get("examples", "").split("\t")
    if examples and all(
        example.startswith("http://www.wikidata.org/entity/") for example in examples
    ):
        # This is a relationship
        return None, None

    for key in [
        "homepage",
        "uri_format_rdf",
        URI_FORMAT_KEY,
        "database",
        "examples",
        "short_names",
    ]:
        if key in bindings:
            bindings[key] = tuple(
                sorted(
                    removeprefix(value, "http://www.wikidata.org/entity/")
                    for value in bindings[key].split("\t")
                )
            )

    for key in ["uri_format_rdf", URI_FORMAT_KEY]:
        if key in bindings:
            bindings[key] = tuple(
                k for k in bindings[key] if k != "http://purl.obolibrary.org/obo/$1"
            )

    # remove URNs
    bindings["uri_format_rdf"] = [
        uri_format_rdf
        for uri_format_rdf in bindings.get("uri_format_rdf", [])
        if not uri_format_rdf.startswith("urn:")
    ]

    for key, canonicals in [
        ("database", CANONICAL_DATABASES),
        ("homepage", CANONICAL_HOMEPAGES),
        ("uri_format", CANONICAL_URI_FORMATS),
        ("uri_format_rdf", CANONICAL_RDF_URI_FORMATS),
    ]:
        # sort by increasing length - the assumption being that the shortest
        # one has the least amount of nonsense, like language tags or extra
        # parameters
        values = sorted(bindings.get(key, []), key=len)
        if not values:
            pass
        elif len(values) == 1:
            bindings[key] = values[0]
        elif prefix not in canonicals:
            logger.debug(
                "[wikidata] need to curate canonical %s for %s (%s):",
                key,
                prefix,
                bindings["name"],
            )
            for value in values:
                logger.debug("  %s", value)
            bindings[key] = values[0]
        else:
            bindings[key] = canonicals[prefix]

    for key in ("uri_format", "uri_format_rdf"):
        if (prefix, bindings.get(key) or None) in URI_FORMAT_BLACKLIST:
            bindings.pop(key)

    pattern = bindings.get("pattern")
    if pattern:
        if not pattern.startswith("^"):
            pattern = "^" + pattern
        if not pattern.endswith("$"):
            pattern = pattern + "$"
        bindings["pattern"] = pattern

    if miriam := bindings.pop("miriam", None):
        bindings.setdefault("xrefs", {})["miriam"] = miriam
    if wikidata_db := bindings.pop("database", None):
        bindings.setdefault("xrefs", {})["wikidata"] = wikidata_db

    return prefix, make_record(bindings)


get_wikidata = build_no_raw_getter(
    processed_path=PROCESSED_PATH,
    func=_get_wikidata,
)


# Unlike the other aligners, the wikidata one doesn't really do the job of making the alignment.
# It's more of a stand-in and curation sheet generator right now.


class WikidataAligner(Aligner):
    """Aligner for Wikidata properties."""

    key = "wikidata"
    getter = get_wikidata

    def get_skip(self) -> Mapping[str, str]:
        """Get entries to skip."""
        return SKIP


if __name__ == "__main__":
    WikidataAligner.cli()
