# -*- coding: utf-8 -*-

"""Download and parse the UniProt Cross-ref database."""

import json
import logging
from typing import Mapping

import requests
from pystow.utils import download

from bioregistry.constants import EXTERNAL, URI_FORMAT_KEY

__all__ = [
    "get_uniprot",
]

logger = logging.getLogger(__name__)

#: Download URL for the UniProt registry
URL = "https://rest.uniprot.org/database/stream?format=json&query=*"
DIRECTORY = EXTERNAL / "uniprot"
DIRECTORY.mkdir(exist_ok=True, parents=True)
RAW_PATH = DIRECTORY / "raw.json"
PROCESSED_PATH = DIRECTORY / "processed.json"

kz = {
    "abbreviation": "{http://purl.uniprot.org/core/}abbreviation",
    "prefix": "{http://purl.org/dc/terms/}identifier",
    "name": "{http://www.w3.org/2000/01/rdf-schema#}label",
    "type": "{http://www.w3.org/1999/02/22-rdf-syntax-ns#}type",
    "primary_topic_of": "{http://xmlns.com/foaf/0.1/}primaryTopicOf",
    "category": "{http://purl.uniprot.org/core/}category",
    "link_is_explicit": "{http://purl.uniprot.org/core/}linkIsExplicit",
    "see_also": "{http://www.w3.org/2000/01/rdf-schema#}seeAlso",
    URI_FORMAT_KEY: "{http://purl.uniprot.org/core/}urlTemplate",
    "citation": "{http://purl.uniprot.org/core/}citation",
    "exact_match": "{http://www.w3.org/2004/02/skos/core#}exactMatch",
    "comment": "{http://www.w3.org/2000/01/rdf-schema#}comment",
}
kzi = {v: k for k, v in kz.items()}

#: resources with these UniProt prefixes don't exist anymore
skip_prefixes = {
    "UniPathway",  # doesn't exist anymore
    "BRENDA",  # has bad format string contains EC, UniProt, and taxon
    "eggNOG",  # not sure what this does
    "PlantReactome",  # incomprehensible URLs
    "Reactome",  # incomprehensible URLs
}


def get_uniprot(force_download: bool = True) -> Mapping[str, Mapping[str, str]]:
    """Get the UniProt registry."""
    if PROCESSED_PATH.is_file() and not force_download:
        with PROCESSED_PATH.open() as file:
            return json.load(file)

    RAW_PATH.write_text(
        json.dumps(requests.get(URL).json(), indent=2, sort_keys=True, ensure_ascii=False)
    )
    rv = {}
    for record in json.loads(RAW_PATH.read_text())["results"]:
        processed_record = _process_record(record)
        if processed_record is None:
            continue
        rv[processed_record.pop("prefix")] = processed_record

    with PROCESSED_PATH.open("w") as file:
        json.dump(rv, file, indent=2, sort_keys=True)
    return rv


def _process_record(record):
    rv = {
        "prefix": record.pop("id"),
        "name": record.pop("name"),
        "abbreviation": record.pop("abbrev"),
        "homepage": record.pop("server"),
        "category": record.pop("category"),
    }
    doi = record.pop("doiId", None)
    pubmed = record.pop("pubMedId", None)
    publication = {}
    if doi:
        publication["doi"] = doi.lower()
    if pubmed:
        publication["pubmed"] = pubmed
    if publication:
        rv["publications"] = [publication]

    del record["linkType"]
    del record["statistics"]
    rv = {k: v for k, v in rv.items() if k and v}

    value = record.pop("dbUrl")
    if "%s" in value and "%u" in value:
        logger.debug(f"has both formats: {value}")
        return None
    else:
        rv[URI_FORMAT_KEY] = value.replace("%s", "$1").replace("%u", "$1")
    if record:
        logger.debug("forgot something: %s", record)
    return rv


if __name__ == "__main__":
    get_uniprot(force_download=False)
