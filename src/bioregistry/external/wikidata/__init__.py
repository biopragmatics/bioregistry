"""Query, download, and format Wikidata as a registry."""

import json
import logging
from collections.abc import Mapping
from pathlib import Path
from textwrap import dedent

from bioregistry.constants import BIOREGISTRY_PATH, URI_FORMAT_KEY
from bioregistry.external.alignment_utils import Aligner
from bioregistry.utils import query_wikidata, removeprefix

__all__ = [
    "WikidataAligner",
    "get_wikidata",
]


logger = logging.getLogger(__name__)

DIRECTORY = Path(__file__).parent.resolve()
PROCESSED_PATH = DIRECTORY / "processed.json"


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
      (GROUP_CONCAT(DISTINCT ?example_; separator='\\t') AS ?example)
      (GROUP_CONCAT(DISTINCT ?short_name_; separator='\\t') AS ?short_name)
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
        ?statement ?propQualifier ?example_ .
        FILTER (STRSTARTS(STR(?propQualifier), "http://www.wikidata.org/prop/qualifier/"))
        FILTER (?propStr = SUBSTR(STR(?propQualifier), 40))
      }
      SERVICE wikibase:label { bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en". }
    }
    GROUP BY ?prop ?propLabel ?propDescription ?miriam ?pattern
    ORDER BY ?prop
    """
)

SKIP = {
    "P3205": "is a relationship",
    "P3781": "is a relationship",
    "P4545": "is a relationship",
    "P3190": "is a relationship",
    "P4954": "is a relationship",
    "P4000": "is a relationship",
    "P3189": "is a relationship",
    "P3310": "is a relationship",
    "P3395": "is a data property",
    "P3387": "is a data property",
    "P3337": "is a data property",
    "P3485": "is a data property",
    "P3486": "is a data property",
    "P10322": "is a data property",
    "P10630": "is a data property",
    "P1193": "is a data property",
    "P1603": "is a data property",
    "P2067": "is a data property",
    "P2844": "is a data property",
    "P2854": "is a data property",
    "P3487": "is a data property",
    "P3492": "is a data property",
    "P4214": "is a data property",
    "P3488": "is a data property",
    "P4250": "is a data property",
    "P574": "is a data property",
    "P7770": "is a data property",
    "P783": "is a data property",
    "P7862": "is a data property",
    "P8010": "is a data property",
    "P8011": "is a data property",
    "P8049": "is a data property",
    "P8556": "is a data property",
    "P9107": "is a data property",
    "Q112586709": "should not be annotated like a property",
    "Q111831044": "should not be annotated like a property",
    "Q115916376": "should not be annotated like a property",
    "P1104": "is a data property",
    "P10676": "is a data property",
    "P181": "is a data property",
    "P1843": "is a data property",
    "P225": "is a data property",
    "P3752": "is a data property",
    "P8558": "is a data property",
    "P6507": "is a data property",
    "P428": "is a data property",
}
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


def _get_mapped():
    return {
        value
        for record in json.loads(BIOREGISTRY_PATH.read_text()).values()
        for metaprefix, value in record.get("mappings", {}).items()
        if metaprefix == "wikidata"
    }


def _get_query(properties) -> str:
    values = " ".join(f"wd:{p}" for p in properties)
    return QUERY_FMT % values


def _get_wikidata():
    """Iterate over Wikidata properties connected to biological databases."""
    mapped = _get_mapped()
    # throw out anything that can be queried directly
    mapped.difference_update(
        bindings["propStr"]["value"]
        for bindings in query_wikidata(PROPERTIES_QUERY)
        if bindings["propStr"]["value"].startswith("P")  # throw away any regular ones
    )
    rv = {}
    for bindings in query_wikidata(_get_query(mapped)):
        bindings = {
            RENAMES.get(key, key): value["value"]
            for key, value in bindings.items()
            if value["value"]
        }
        prefix = bindings["prefix"] = removeprefix(
            bindings["prefix"], "http://www.wikidata.org/entity/"
        )
        if prefix in SKIP:
            continue

        examples = bindings.get("example", "").split("\t")
        if examples and all(
            example.startswith("http://www.wikidata.org/entity/") for example in examples
        ):
            # This is a relationship
            continue

        for key in [
            "homepage",
            "uri_format_rdf",
            URI_FORMAT_KEY,
            "database",
            "example",
            "short_name",
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
                logger.warning(
                    "[wikidata] need to curate canonical %s for %s (%s):",
                    key,
                    prefix,
                    bindings["name"],
                )
                for value in values:
                    logger.warning("  %s", value)
                bindings[key] = values[0]
            else:
                bindings[key] = canonicals[prefix]

        pattern = bindings.get("pattern")
        if pattern:
            if not pattern.startswith("^"):
                pattern = "^" + pattern
            if not pattern.endswith("$"):
                pattern = pattern + "$"
            bindings["pattern"] = pattern

        rv[prefix] = {k: v for k, v in bindings.items() if k and v}

    return rv


def get_wikidata(force_download: bool = False):
    """Get the wikidata registry."""
    if PROCESSED_PATH.exists() and not force_download:
        with PROCESSED_PATH.open() as file:
            return json.load(file)

    data = _get_wikidata()
    with PROCESSED_PATH.open("w") as file:
        json.dump(data, file, indent=2, sort_keys=True)
    return data


# Unlike the other aligners, the wikidata one doesn't really do the job of making the alignment.
# It's more of a stand-in and curation sheet generator right now.


class WikidataAligner(Aligner):
    """Aligner for Wikidata properties."""

    key = "wikidata"
    getter = get_wikidata
    curation_header = ("name", "homepage", "description", "uri_format", "example")

    def get_skip(self) -> Mapping[str, str]:
        """Get entries to skip."""
        return SKIP


if __name__ == "__main__":
    WikidataAligner.cli()
