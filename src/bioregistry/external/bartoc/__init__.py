# -*- coding: utf-8 -*-

"""Download the BARTOC registry."""

import json
from pathlib import Path
from typing import Any, Mapping

import requests
from tqdm import tqdm

from bioregistry.constants import URI_FORMAT_KEY
from bioregistry.license_standardizer import standardize_license

from ..alignment_utils import Aligner

__all__ = [
    "get_bartoc",
    "BartocAligner",
]

HERE = Path(__file__).parent.resolve()
PROCESSED_PATH = HERE / "processed.json"
URL = "https://bartoc.org/data/dumps/latest.ndjson"


def get_bartoc(force_download: bool = True) -> Mapping[str, Mapping[str, Any]]:
    """Get the BARTOC registry.

    :param force_download: If true, forces download. If false and the file
        is already cached, reuses it.
    :returns: The BARTOC registry

    .. seealso:: https://bartoc.org/
    """
    if PROCESSED_PATH.is_file() and not force_download:
        return json.loads(PROCESSED_PATH.read_text())
    rv = {}
    for line in requests.get(URL).iter_lines():
        record = json.loads(line)
        record = _process_bartoc_record(record)
        rv[record["prefix"]] = record

    PROCESSED_PATH.write_text(json.dumps(rv, indent=2, ensure_ascii=False, sort_keys=True))
    return rv


def _process_bartoc_record(record: dict[str, Any]) -> dict[str, Any]:
    prefix = record["uri"][len("http://bartoc.org/en/node/") :]
    rv = {
        "prefix": prefix,
        "description": record.get("definition", {}).get("en", [""])[0].strip('"').strip(),
        "homepage": record.get("url", "").strip(),
        "name": record.get("prefLabel", {}).get("en", "").strip(),
    }
    pattern = record.get("notationPattern")
    if pattern:
        rv["pattern"] = "^" + pattern.strip().lstrip("^").rstrip("$") + "$"

    for identifier in record.get("identifier", []):
        if identifier.startswith("http://www.wikidata.org/entity/"):
            rv["wikidata_database"] = identifier[len("http://www.wikidata.org/entity/") :]

    abbreviations = record.get("notation")
    if abbreviations:
        if len(abbreviations) > 1:
            tqdm.write(f"[bartoc:{prefix}] got multiple abbr.: {abbreviations}")
        abbreviation = abbreviations[0].strip()
        if " " in abbreviation:
            tqdm.write(f"[bartoc:{prefix}] space in abbr.: {abbreviation}")
        rv["abbreviation"] = abbreviation

    for license_dict in record.get("license", []):
        license_key = standardize_license(license_dict["uri"].strip())
        if license_key:
            rv["license"] = license_key

    uri_pattern = record.get("uriPattern")
    if uri_pattern and "(" in uri_pattern and ")" in uri_pattern:
        left_pos = uri_pattern.find("(")
        right_pos = uri_pattern.find(")")
        rv[URI_FORMAT_KEY] = uri_pattern[:left_pos] + "$1" + uri_pattern[1 + right_pos :]

    return {k: v for k, v in rv.items() if k and v}


class BartocAligner(Aligner):
    """Aligner for BARTOC."""

    key = "bartoc"
    getter = get_bartoc
    alt_key_match = "abbreviation"
    curation_header = ["name", "homepage", "description"]


if __name__ == "__main__":
    BartocAligner.cli()
