# -*- coding: utf-8 -*-

"""Query, download, and format Wikidata as a registry."""

import json
import logging
from textwrap import dedent
from typing import Dict

import click

from bioregistry.constants import EXTERNAL, URI_FORMAT_KEY
from bioregistry.utils import query_wikidata, removeprefix

__all__ = [
    "get_wikidata",
]

DIRECTORY = EXTERNAL / "wikidata"
DIRECTORY.mkdir(exist_ok=True, parents=True)
RAW_PATH = DIRECTORY / "raw.json"
PROCESSED_PATH = DIRECTORY / "processed.json"

logger = logging.getLogger(__name__)

#: A query to wikidata for properties related to chemistry, biology, and related
QUERY = dedent(
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
      VALUES ?category {
        wd:Q21294996  # chemistry
        wd:Q22988603  # biology
      }
      ?prop wdt:P31/wdt:P279+ ?category .
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

RENAMES = {"propLabel": "name", "propDescription": "description"}
CANONICAL_DATABASES = {
    "P6800": "Q87630124",  # -> NCBI Genome
    "P627": "Q48268",  # -> International Union for Conservation of Nature
    "P351": "Q1345229",  # NCBI Gene
    "P4168": "Q112783946",  # Immune epitope database
}

CANONICAL_HOMEPAGES: Dict[str, str] = {}
CANONICAL_URI_FORMATS = {
    "P830": "https://eol.org/pages/$1",
    "P2085": "https://jglobal.jst.go.jp/en/redirect?Nikkaji_No=$1",
}

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


def _get_wikidata():
    """Iterate over Wikidata properties connected to biological databases."""
    rv = {}
    for bindings in query_wikidata(QUERY):
        examples = bindings.get("example", {}).get("value", "").split("\t")
        if examples and all(
            example.startswith("http://www.wikidata.org/entity/") for example in examples
        ):
            # This is a relationship
            continue

        bindings = {
            RENAMES.get(key, key): value["value"]
            for key, value in bindings.items()
            if value["value"]
        }

        prefix = bindings["prefix"] = removeprefix(
            bindings["prefix"], "http://www.wikidata.org/entity/"
        )
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

        for key, canonicals in [
            ("database", CANONICAL_DATABASES),
            ("homepage", CANONICAL_HOMEPAGES),
            ("uri_format", CANONICAL_URI_FORMATS),
        ]:
            values = bindings.get(key, [])
            if not values:
                pass
            elif len(values) == 1:
                bindings[key] = values[0]
            elif prefix not in canonicals:
                logger.warning(f"need to curate canonical {key} for {prefix}: {', '.join(values)}")
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

        rv[prefix] = bindings

    return rv


def get_wikidata(force_download: bool = False):
    """Get the wikidata registry."""
    if PROCESSED_PATH.exists() and not force_download:
        with PROCESSED_PATH.open() as file:
            return json.load(file)

    data = _get_wikidata()
    with RAW_PATH.open("w") as file:
        json.dump(data, file, indent=2, sort_keys=True)
    return data


@click.command()
def _main():
    data = get_wikidata(force_download=True)
    click.echo(f"Got {len(data):,} records")


if __name__ == "__main__":
    _main()
