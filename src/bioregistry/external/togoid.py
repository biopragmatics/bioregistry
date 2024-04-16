# -*- coding: utf-8 -*-

"""Download TogoID."""

import json
from typing import Dict

import requests
import yaml

from bioregistry.constants import EXTERNAL, URI_FORMAT_KEY

__all__ = [
    "get_togoid",
]

DIRECTORY = EXTERNAL / "togoid"
DIRECTORY.mkdir(exist_ok=True, parents=True)
RAW_PATH = DIRECTORY / "raw.json"
PROCESSED_PATH = DIRECTORY / "processed.json"

ONTOLOGY_URL = (
    "https://raw.githubusercontent.com/togoid/togoid-config/main/ontology/togoid-ontology.ttl"
)
DATASET_URL = "https://raw.githubusercontent.com/togoid/togoid-config/main/config/dataset.yaml"


def _get_ontology() -> Dict[str, str]:
    import rdflib

    graph = rdflib.Graph()
    graph.parse(ONTOLOGY_URL, format="turtle")
    rows = graph.query("SELECT ?namespace ?prefix WHERE { ?namespace dcterms:identifier ?prefix }")
    return {
        str(prefix): namespace.removeprefix("http://togoid.dbcls.jp/ontology#")
        for namespace, prefix in rows
    }


def _get_dataset():
    data = yaml.safe_load(requests.get(DATASET_URL).text)
    rv = {}
    for prefix, record in data.items():
        name = record.get("label")
        if not name:
            continue
        rr = {
            "name": name,
            "pattern": record["regex"].replace("<id>", ""),
            URI_FORMAT_KEY: record["prefix"] + "$1",  # this is right, they named it weird
        }
        examples_lists = record.get("examples", [])
        if examples_lists:
            rr["examples"] = examples_lists[0]
        category = record.get("category")
        if category:
            rr["keywords"] = [category]
        integbio_catalog_id = record.get("catalog")
        if integbio_catalog_id and integbio_catalog_id != "FIXME":
            rr["integbio"] = integbio_catalog_id
        rv[prefix] = rr
    return rv


def get_togoid(*, force_download: bool = False, force_refresh: bool = False):
    """Get the TogoID data."""
    if PROCESSED_PATH.exists() and not force_refresh:
        with PROCESSED_PATH.open() as file:
            return json.load(file)

    key_to_prefix = _get_ontology()
    records = _get_dataset()
    rv = {
        key_to_prefix[key]: record | {"prefix": key_to_prefix[key]}
        for key, record in records.items()
    }

    with PROCESSED_PATH.open("w") as file:
        json.dump(rv, file, indent=2, sort_keys=True)
    return rv


if __name__ == "__main__":
    get_togoid(force_refresh=True)
