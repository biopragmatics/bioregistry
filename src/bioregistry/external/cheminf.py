# -*- coding: utf-8 -*-

"""Download the Chemical Information Ontology registry (children of ``CHEMINF:000464``).

To convert CHEMINF from OWL to OBO Graph JSON, do the following:

.. code-block:: sh

    $ robot convert --input cheminf.owl --format json --output cheminf.json

See the OBO Foundry workflow for preparing a docker container that has ROBOT available
"""

import json

import requests

from bioregistry.data import EXTERNAL

__all__ = [
    "get_cheminf",
]

DIRECTORY = EXTERNAL / "cheminf"
DIRECTORY.mkdir(exist_ok=True, parents=True)
PROCESSED_PATH = DIRECTORY / "processed.json"

EXTERNAL_IRI = "http%253A%252F%252Fsemanticscience.org%252Fresource%252FCHEMINF_000464"
BASE_URL = f"https://www.ebi.ac.uk/ols/api/ontologies/cheminf/terms/{EXTERNAL_IRI}/descendants"


def get_cheminf(force_download: bool = False):
    """Get the the Chemical Information Ontology registry."""
    if PROCESSED_PATH.exists() and not force_download:
        with PROCESSED_PATH.open() as file:
            return json.load(file)
    res = requests.get(BASE_URL).json()
    rv = {}
    for term in res["_embedded"]["terms"]:
        identifier = term["obo_id"][len("CHEMINF:") :]
        description = term.get("description")
        rv[identifier] = {
            "name": _clean(term["label"]),
            "description": description and description[0],
            "obsolete": term.get("is_obsolete", False),
        }
    with PROCESSED_PATH.open("w") as file:
        json.dump(rv, file, indent=2, sort_keys=True)
    return rv


def _clean(s: str) -> str:
    if s.endswith("identifier"):
        s = s[: -len("identifier")].strip()
    return s


if __name__ == "__main__":
    get_cheminf(force_download=True)
