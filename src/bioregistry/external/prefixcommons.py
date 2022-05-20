# -*- coding: utf-8 -*-

"""Download registry information from the Life Science Registry (LSR), which powers Prefix Commons.

.. seealso::

    - http://tinyurl.com/lsregistry which should expand to
      https://docs.google.com/spreadsheets/d/1cDGJcRteb9F5-jbw7Q7np0kk4hfWhdBHNYRIg3LXDrs/edit#gid=0
"""

import json
from typing import Any, Dict

from pystow.utils import download

from bioregistry.constants import EXTERNAL

__all__ = [
    "get_prefixcommons",
]

DIRECTORY = EXTERNAL / "prefixcommons"
DIRECTORY.mkdir(exist_ok=True, parents=True)
RAW_PATH = DIRECTORY / "raw.tsv"
PROCESSED_PATH = DIRECTORY / "processed.json"
GOOGLE_DOCUMENT_ID = "1c4DmQqTGS4ZvJU_Oq2MFnLk-3UUND6pWhuMoP8jgZhg"
URL = f"https://docs.google.com/spreadsheets/d/{GOOGLE_DOCUMENT_ID}/export?format=tsv&gid=0"
COLUMNS = [
    "prefix",  # "Preferred Prefix",
    "Alt-prefix",
    "Provider Base URI",
    "Alternative Base URI",
    "MIRIAM",
    "BiodbcoreID",
    "bioportal",  # "BioPortal Ontology ID",
    "miriam",  # "identifiers.org",
    "Abbreviation",
    "name",  # originally: Title,
    "description",  # "Description",
    "pubmed_ids",  # "PubMed ID"
    "Organization",
    "Type (warehouse, dataset or terminology)",
    "keywords",
    "homepage",  # "Homepage",
    "Functional?",
    "sub-namespace in dataset",
    "part of collection",
    "License URL",
    "License Text",
    "Rights",
    "pattern",  # "ID regex",
    "example",  # "ExampleID",
    "uri_format",  # "Provider HTML URL",
    "",
    "MIRIAM checked",
    "MIRIAM curator notes",
    "MIRIAM coverage",
    "updates",
    "year last accessible",
    "wayback url",
    "last updated",
    "last updated by",
    "last updated by (orcid)",
]
KEEP = {
    "prefix",
    "bioportal",
    "miriam",
    "name",
    "description",
    "pubmed_ids",
    "keywords",
    "homepage",
    "pattern",
    "example",
    "uri_format",
}


def get_prefixcommons(force_download: bool = False):
    """Get the Life Science Registry."""
    if PROCESSED_PATH.exists() and not force_download:
        with PROCESSED_PATH.open() as file:
            return json.load(file)

    download(url=URL, path=RAW_PATH, force=True)
    rows = {}
    with RAW_PATH.open() as file:
        lines = iter(file)
        next(lines)  # throw away header
        for line in lines:
            prefix, data = _process_row(line)
            if prefix and data:
                rows[prefix] = data

    PROCESSED_PATH.write_text(json.dumps(rows, sort_keys=True, indent=2))
    return rows


def _process_row(line: str):
    cells = line.strip().split("\t")
    cells_processed = [None if cell in {"N/A"} else cell for cell in cells]
    rv: Dict[str, Any] = {
        key: value.strip()
        for key, value in zip(COLUMNS, cells_processed)
        if key and value and key in KEEP
    }
    for key in ["name", "description", "example", "pattern"]:
        if not rv.get(key):
            return None, None

    for key in ["keywords", "pubmed_ids"]:
        values = rv.get(key)
        if values:
            rv[key] = [value.strip() for value in values.split(",")]

    uri_format = rv.get("uri_format")
    if uri_format:
        rv["uri_format"] = uri_format.replace("$id", "$1")

    pattern = rv.get("pattern")
    if pattern:
        if not pattern.startswith("^"):
            pattern = f"^{pattern}"
        if not pattern.endswith("$"):
            pattern = f"{pattern}$"
        rv["pattern"] = pattern

    return cells[0], rv


if __name__ == "__main__":
    print(len(get_prefixcommons(force_download=True)))  # noqa:T201
