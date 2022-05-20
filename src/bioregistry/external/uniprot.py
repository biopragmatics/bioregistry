# -*- coding: utf-8 -*-

"""Download and parse the UniProt Cross-ref database."""

import json
import logging
from typing import Mapping

from defusedxml import ElementTree
from pystow.utils import download

from bioregistry.constants import EXTERNAL, URI_FORMAT_KEY

__all__ = [
    "get_uniprot",
]

logger = logging.getLogger(__name__)

#: Download URL for the UniProt registry
URL = "https://www.uniprot.org/database/?format=rdf"
DIRECTORY = EXTERNAL / "uniprot"
DIRECTORY.mkdir(exist_ok=True, parents=True)
RAW_PATH = DIRECTORY / "raw.xml"
PROCESSED_PATH = DIRECTORY / "processed.json"

kz = {
    "prefix": "{http://purl.uniprot.org/core/}abbreviation",
    "identifier": "{http://purl.org/dc/terms/}identifier",
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


def get_uniprot(force_download: bool = True) -> Mapping[str, Mapping[str, str]]:
    """Get the UniProt registry."""
    if PROCESSED_PATH.is_file() and not force_download:
        with PROCESSED_PATH.open() as file:
            return json.load(file)
    download(url=URL, path=RAW_PATH, force=True)
    with RAW_PATH.open() as file:
        tree = ElementTree.parse(file)
    root = tree.getroot()
    rv = {}
    for element in root.findall("{http://www.w3.org/1999/02/22-rdf-syntax-ns#}Description"):
        entry = {}
        for key, path in kz.items():
            value = element.findtext(path)
            if not value:
                continue
            if key == URI_FORMAT_KEY:
                if "%s" in value and "%u" in value:
                    pass  # FIXME
                else:
                    value = value.replace("%s", "$1").replace("%u", "$1")
            entry[key] = value
        prefix = entry.get("prefix")
        if prefix is not None:
            rv[prefix] = entry

    with PROCESSED_PATH.open("w") as file:
        json.dump(rv, file, indent=2)
    return rv


if __name__ == "__main__":
    get_uniprot(force_download=True)
