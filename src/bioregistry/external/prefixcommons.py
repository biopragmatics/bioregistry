# -*- coding: utf-8 -*-

"""Download registry information from the Life Science Registry (LSR), which powers Prefix Commons.

.. seealso::

    - http://tinyurl.com/lsregistry which should expand to
      https://docs.google.com/spreadsheets/d/1cDGJcRteb9F5-jbw7Q7np0kk4hfWhdBHNYRIg3LXDrs/edit#gid=0
"""

import json
import logging
from typing import Any, Dict, List

from pystow.utils import download

from bioregistry.constants import EXTERNAL
from bioregistry.license_standardizer import standardize_license

__all__ = [
    "get_prefixcommons",
]

logger = logging.getLogger(__name__)

DIRECTORY = EXTERNAL / "prefixcommons"
DIRECTORY.mkdir(exist_ok=True, parents=True)
RAW_PATH = DIRECTORY / "raw.tsv"
PROCESSED_PATH = DIRECTORY / "processed.json"
GOOGLE_DOCUMENT_ID = "1c4DmQqTGS4ZvJU_Oq2MFnLk-3UUND6pWhuMoP8jgZhg"
URL = f"https://docs.google.com/spreadsheets/d/{GOOGLE_DOCUMENT_ID}/export?format=tsv&gid=0"
COLUMNS = [
    "prefix",  # "Preferred Prefix",
    "synonyms",
    "rdf_uri_prefix",  # this is the RDF-useful version
    "alternate_uri_formats",  # these are alternative URI prefixes
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
    "part_of",  # sub-namespace in dataset
    "part of collection",
    "license_url",
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
    "synonyms",
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
    "license_url",
    "alternate_uri_formats",
    "rdf_uri_prefix",
}
#: These contain synonyms with mismatches
DISCARD_SYNONYMS = {"biogrid", "cath", "zfa"}
SKIP_URI_FORMATS = {
    "http://purl.obolibrary.org/obo/$1",
    "http://www.ebi.ac.uk/ontology-lookup/?termId=$1",
    "http://arabidopsis.org/servlets/TairObject?accession=$1",
}


def get_prefixcommons(force_download: bool = False, force_process: bool = False):
    """Get the Life Science Registry."""
    if PROCESSED_PATH.exists() and not (force_download or force_process):
        with PROCESSED_PATH.open() as file:
            return json.load(file)

    download(url=URL, path=RAW_PATH, force=force_download)
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
    prefix = cells[0]
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

    synonyms = rv.pop("synonyms", None)
    if not synonyms:
        pass
    elif prefix in DISCARD_SYNONYMS:
        pass
    else:
        synonyms_it = [s.strip() for s in synonyms.split(",")]
        synonyms_it = [
            synonym
            for synonym in synonyms_it
            if synonym.lower() != prefix.lower() and " " not in synonym
        ]
        if synonyms_it:
            rv["synonyms"] = synonyms_it

    license_url = rv.pop("license_url", None)
    if license_url:
        rv["license"] = standardize_license(license_url)

    uri_format = rv.pop("uri_format", None)
    if uri_format:
        uri_format = uri_format.replace("$id", "$1").replace("[?id]", "$1").replace("$d", "$1")
        if uri_format not in SKIP_URI_FORMATS:
            rv["uri_format"] = uri_format

    uri_rdf_formats = _get_uri_formats(rv, "rdf_uri_prefix")
    if uri_rdf_formats:
        if len(uri_rdf_formats) > 1:
            logger.warning("got multiple RDF formats for %s", prefix)
        rv["rdf_uri_format"] = uri_rdf_formats[0]

    alt_uri_formats_clean = _get_uri_formats(rv, "alternate_uri_formats")
    if alt_uri_formats_clean:
        rv["alt_uri_formats"] = alt_uri_formats_clean

    pattern = rv.get("pattern")
    if pattern:
        if not pattern.startswith("^"):
            pattern = f"^{pattern}"
        if not pattern.endswith("$"):
            pattern = f"{pattern}$"
        rv["pattern"] = pattern

    return prefix, rv


def _get_uri_formats(rv, key) -> List[str]:
    uri_formats = rv.pop(key, None)
    if not uri_formats:
        return []
    rv = []
    for uri_format in uri_formats.split(","):
        uri_format = uri_format.strip()
        if not uri_format:
            continue
        if "identifiers.org" in uri_format:  # FIXME some non-miriam resources might use this
            continue
        if "obofoundry.org" in uri_format:  # FIXME some non-obo resources might use this
            continue
        if "obolibrary.org" in uri_format:  # FIXME take this check out
            continue
        if "$1" in uri_format or "[?id]" in uri_format:  # FIXME check if these come at the end
            continue
        uri_format = f"{uri_format}$1"
        if uri_format in SKIP_URI_FORMATS:
            continue
        rv.append(uri_format)
    return rv


if __name__ == "__main__":
    print(len(get_prefixcommons(force_process=True, force_download=True)))  # noqa:T201
