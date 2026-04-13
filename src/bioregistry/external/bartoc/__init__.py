"""Download the BARTOC registry."""

import json
import logging
from collections import defaultdict
from collections.abc import Sequence
from pathlib import Path
from typing import Any, ClassVar

from bioregistry.constants import RAW_DIRECTORY, URI_FORMAT_KEY
from bioregistry.license_standardizer import standardize_license

from ..alignment_utils import Aligner, build_getter
from ...alignment_model import License, Record, make_record

__all__ = [
    "BartocAligner",
    "get_bartoc",
    "get_bartoc_registries",
]

logger = logging.getLogger(__name__)

HERE = Path(__file__).parent.resolve()
RAW_PATH = RAW_DIRECTORY.joinpath("bartoc.jsonl")
PROCESSED_PATH = HERE / "processed.json"
URL = "https://bartoc.org/data/dumps/latest.ndjson"

URI_PREFIX = "http://bartoc.org/en/node/"


def process_bartoc(path: Path) -> dict[str, Record]:
    """Process BARTOC."""
    rv = {}
    with path.open() as file:
        for line in file:
            data = json.loads(line)
            prefix = data["uri"][len(URI_PREFIX) :]
            rv[prefix] = _process_bartoc_record(prefix, data)
    return rv


get_bartoc = build_getter(
    processed_path=PROCESSED_PATH, raw_path=RAW_PATH, url=URL, func=process_bartoc
)

URI_FORMAT_SKIPS: dict[str, str] = {
    "18653": "all LIDO records are overlapping",
    "18654": "all LIDO records are overlapping",
    "18655": "all LIDO records are overlapping",
    "18656": "all LIDO records are overlapping",
    "18657": "all LIDO records are overlapping",
    "18658": "all LIDO records are overlapping",
    "18659": "all LIDO records are overlapping",
    "18660": "all LIDO records are overlapping",
}


def _process_bartoc_record(prefix: str, record: dict[str, Any]) -> Record:
    rv = {
        "description": record.get("definition", {}).get("en", [""])[0].strip('"').strip(),
        "homepage": record.get("url", "").strip(),
        "name": record.get("prefLabel", {}).get("en", "").strip(),
    }
    pattern = record.get("notationPattern")
    if pattern:
        rv["pattern"] = "^" + pattern.strip().lstrip("^").rstrip("$") + "$"

    # FIXME what about external mappings?
    for identifier in record.get("identifier", []):
        if identifier.startswith("http://www.wikidata.org/entity/"):
            rv.setdefault("xrefs", {})["wikidata"] = identifier[
                len("http://www.wikidata.org/entity/") :
            ]

    for short_name in record.get("notation", []):
        short_name = short_name.strip()
        if " " in short_name:
            logger.debug(f"[bartoc:{prefix}] space in abbr.: {short_name}")
        rv.setdefault("short_names", []).append(short_name)

    for license_dict in record.get("license", []):
        license_url = license_dict["uri"].strip()
        license_key = standardize_license(license_url)
        if license_key:
            rv["license"] = License(url=license_url, spdx=license_key)

    if prefix in URI_FORMAT_SKIPS:
        pass
    elif uri_prefix := record.pop("namespace", None):
        rv[URI_FORMAT_KEY] = uri_prefix.strip() + "$1"
    elif uri_pattern := record.get("uriPattern"):
        if "(" not in uri_pattern and ")" not in uri_pattern:
            logger.debug(f"bad URI pattern: {uri_pattern}, assuming is URI prefix")
            rv[URI_FORMAT_KEY] = uri_pattern.strip() + "$1"
        else:
            left_pos = uri_pattern.find("(")
            right_pos = uri_pattern.find(")")
            rv[URI_FORMAT_KEY] = uri_pattern[:left_pos] + "$1" + uri_pattern[1 + right_pos :]

    if examples := record.pop("EXAMPLES", []):
        rv["examples"] = [example.strip() for example in examples]

    return make_record(rv)


def get_bartoc_registries() -> dict[str, set[str]]:
    """Get a mapping from registries to their parts.

    :returns: A mapping from BARTOC ID for a registry to BARTOC ID for an entry in the registry.

    For example, the `NFDI4Objects Terminologies <http://bartoc.org/en/node/18961>`_
    list will be a key of ``18961`` and have values listed on this search
    page: https://bartoc.org/vocabularies/?sort=relevance&order=desc&limit=10&filter=in%3Ahttp%3A%2F%2Fbartoc.org%2Fen%2Fnode%2F18961
    """
    rv: defaultdict[str, set[str]] = defaultdict(set)
    with RAW_PATH.open() as file:
        for line in file:
            data = json.loads(line)
            identifier = data["uri"].removeprefix(URI_PREFIX)
            for part in data.get("partOf", []):
                rv[part["uri"].removeprefix(URI_PREFIX)].add(identifier)
    return dict(rv)


class BartocAligner(Aligner):
    """Aligner for BARTOC."""

    key = "bartoc"
    getter = get_bartoc
    alt_key_match = "abbreviation"  # or short_name
    curation_header: ClassVar[Sequence[str]] = ["name", "homepage", "description"]


if __name__ == "__main__":
    BartocAligner.cli()
