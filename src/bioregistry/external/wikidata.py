# -*- coding: utf-8 -*-

"""Query, download, and format Wikidata as a registry."""

import json
import logging
from collections import defaultdict
from textwrap import dedent

from bioregistry.data import EXTERNAL
from bioregistry.utils import query_wikidata

__all__ = [
    "get_wikidata",
]

DIRECTORY = EXTERNAL / "wikidata"
DIRECTORY.mkdir(exist_ok=True, parents=True)
RAW_PATH = DIRECTORY / "raw.json"
PROCESSED_PATH = DIRECTORY / "processed.json"

logger = logging.getLogger(__name__)

HEADER = {
    # 'database',
    "databaseLabel": "database.label",
    "databaseMiriam": "database.miriam",
    "databaseHomepage": "database.homepage",
    "prop": "prefix",
    "propLabel": "name",
    "propMiriam": "miriam",
    "propHomepage": "homepage",
    "propFormat": "format",
    "propFormatRDF": "format.rdf",
    "propPattern": "pattern",
}


def iter_results():
    """Iterate over Wikidata properties connected to biological databases."""
    query = dedent(
        """\
    SELECT
        ?database ?databaseLabel ?databaseMiriam ?databaseHomepage
        ?prop ?propLabel ?propMiriam ?propHomepage ?propFormat ?propFormatRDF ?propPattern
        # ?propDatabase ?propDatabaseLabel
    WHERE {
        ?database wdt:P31 wd:Q4117139 .
        ?database wdt:P1687 ?prop .
        OPTIONAL { ?database wdt:P856 ?databaseHomepage } .
        OPTIONAL { ?database wdt:P4793 ?databaseMiriam } .
        OPTIONAL { ?prop wdt:P4793 ?propMiriam } .
        OPTIONAL { ?prop wdt:P1630 ?propFormat } .
        OPTIONAL { ?prop wdt:P1921 ?propFormatRDF } .
        OPTIONAL { ?prop wdt:P1793 ?propPattern } .
        OPTIONAL { ?prop wdt:P1896 ?propHomepage } .
        OPTIONAL { ?prop wdt:P1629 ?propDatabase } .
        SERVICE wikibase:label { bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en". }
    }
    ORDER BY DESC(?databaseLabel)
    """
    )
    # Q4117139 "biological database"
    # P31 "instance of"
    # P1687 "wikidata property" <- meta property
    for bindings in query_wikidata(query):
        for url in ["prop", "propDatabase", "database"]:
            if url in bindings:
                bindings[url]["value"] = bindings[url]["value"].split("/")[-1]
        yield {key: value["value"] for key, value in bindings.items()}


# Stuff with miriam IDs that shouldn't
MIRIAM_BLACKLIST = {
    "Q51162088",
    "Q56221155",
    "Q47519952",
    "Q106201514",
    "Q106201090",
    "Q106201991",
    "Q106201090",
    "Q106201514",
    "Q106201904",
    "Q106201991",
    "Q106832467",
    "Q96212863",
    "Q106695243",
    "Q51162088",
    "Q56221155",
    "Q47519952",
}


def get_wikidata(force_download: bool = False):
    """Get the wikidata registry."""
    if PROCESSED_PATH.exists() and not force_download:
        with PROCESSED_PATH.open() as file:
            return json.load(file)

    data = list(iter_results())
    with RAW_PATH.open("w") as file:
        json.dump(data, file, indent=2, sort_keys=True)

    agg1 = defaultdict(list)
    for record in data:
        agg1[record["prop"]].append(record)

    agg2 = {key: _aggregate(key, values) for key, values in agg1.items()}
    rv = {key: _process(record) for key, record in agg2.items()}
    with PROCESSED_PATH.open("w") as file:
        json.dump(rv, file, indent=2, sort_keys=True)
    return rv


CANONICAL_DATABASES = {
    "P6800": "Q87630124",  # -> NCBI Genome
    "P627": "Q48268",  # -> International Union for Conservation of Nature
}


def _process(record):
    return {HEADER.get(k, k): v for k, v in record.items()}


def _aggregate(prop, records):
    databases = {record["database"]: record["databaseLabel"] for record in records}
    if len(databases) == 1:
        canonical_database = list(databases)[0]
    elif prop not in CANONICAL_DATABASES:
        raise ValueError(f"need to curate which is the canonical database for {prop}: {databases}")
    else:
        canonical_database = CANONICAL_DATABASES[prop]

    records = [
        dict(record_tuple)
        for record_tuple in sorted(
            {
                tuple(sorted(record.items()))
                for record in records
                if record["database"] == canonical_database and record["prop"] == prop
            }
        )
    ]

    if len(records) == 1:
        return records[0]

    # Throw my hands up in the air! It's probably just because of different URI formatters.
    return records[0]


if __name__ == "__main__":
    # from tabulate import tabulate
    # print(list(iter_wikidata()))
    r = get_wikidata(force_download=True)
    print(f"Got {len(r)} records")
