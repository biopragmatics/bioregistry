"""Download TogoID."""

from collections.abc import Sequence
from pathlib import Path
from typing import ClassVar

import requests
import yaml

from bioregistry.alignment_model import Record, dump_records, load_processed
from bioregistry.constants import RAW_DIRECTORY, URI_FORMAT_KEY
from bioregistry.external.alignment_utils import Aligner

__all__ = [
    "TogoIDAligner",
    "get_togoid",
]


DIRECTORY = Path(__file__).parent.resolve()
RAW_PATH = RAW_DIRECTORY / "togoid.json"
PROCESSED_PATH = DIRECTORY / "processed.json"

ONTOLOGY_URL = (
    "https://raw.githubusercontent.com/togoid/togoid-config/main/ontology/togoid-ontology.ttl"
)
DATASET_URL = "https://raw.githubusercontent.com/togoid/togoid-config/main/config/dataset.yaml"
DATASET_DESCRIPTIONS_URL = "https://api.togoid.dbcls.jp/config/descriptions"


def _get_ontology() -> dict[str, str]:
    import rdflib

    graph = rdflib.Graph()
    graph.parse(ONTOLOGY_URL, format="turtle")
    rows = graph.query("SELECT ?namespace ?prefix WHERE { ?namespace dcterms:identifier ?prefix }")
    return {
        str(prefix): namespace.removeprefix("http://togoid.dbcls.jp/ontology#")
        for namespace, prefix in rows
    }


def _get_descriptions() -> dict[str, str]:
    res = requests.get(DATASET_DESCRIPTIONS_URL, timeout=15)

    # Replace \r\n and \r or \n individually with a single space
    def _sanitize_description(description: str) -> str:
        return description.replace("\r\n", " ").replace("\r", " ").replace("\n", " ")

    return {
        key: _sanitize_description(entry["description_en"])
        for key, entry in res.json().items()
        if "description_en" in entry
    }


def get_togoid(*, force_download: bool = False, force_refresh: bool = False) -> dict[str, Record]:
    """Get the TogoID data."""
    if PROCESSED_PATH.exists() and not force_refresh:
        return load_processed(PROCESSED_PATH)

    key_to_prefix = _get_ontology()
    key_to_description = _get_descriptions()

    res = requests.get(DATASET_URL, timeout=15)
    data = yaml.safe_load(res.text)
    rv = {}
    for key, record in data.items():
        prefix = key_to_prefix[key]
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
            rr["catalog"] = integbio_catalog_id

        description = key_to_description.get(key)
        if description:
            rr["description"] = description

        rv[prefix] = Record.model_validate(rr)

    dump_records(rv, PROCESSED_PATH)
    return rv


class TogoIDAligner(Aligner):
    """Aligner for TogoID."""

    key = "togoid"
    getter = get_togoid
    curation_header: ClassVar[Sequence[str]] = ("name", "uri_format")


if __name__ == "__main__":
    TogoIDAligner.cli()
