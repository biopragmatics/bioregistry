"""Download Biolink."""

import json
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import ClassVar

import yaml

from bioregistry.alignment_model import Record
from bioregistry.constants import RAW_DIRECTORY, URI_FORMAT_KEY
from bioregistry.external.alignment_utils import Aligner, build_getter

__all__ = [
    "BiolinkAligner",
    "get_biolink",
    "parse_biolink_raw",
]

URL = "https://raw.githubusercontent.com/biolink/biolink-model/master/biolink-model.yaml"

DIRECTORY = Path(__file__).parent.resolve()
RAW_PATH = RAW_DIRECTORY / "biolink.yaml"
PROCESSED_PATH = DIRECTORY / "processed.json"

PROCESSING_BIOLINK_PATH = DIRECTORY / "processing_biolink.json"


def parse_biolink_raw(path: Path) -> dict[str, Record]:
    """Parse BioLink raw data."""
    with path.open() as file:
        data = yaml.safe_load(file)
    rv = {
        prefix: Record(uri_format=f"{uri_prefix}$1")
        for prefix, uri_prefix in data["prefixes"].items()
    }
    return rv


get_biolink = build_getter(
    processed_path=PROCESSED_PATH,
    raw_path=RAW_PATH,
    url=URL,
    func=parse_biolink_raw,
)


class BiolinkAligner(Aligner):
    """Aligner for Biolink."""

    key = "biolink"
    getter = get_biolink
    curation_header: ClassVar[Sequence[str]] = [URI_FORMAT_KEY]

    def get_skip(self) -> Mapping[str, str]:
        """Get the skipped Biolink identifiers."""
        with PROCESSING_BIOLINK_PATH.open() as file:
            j = json.load(file)
        return {entry["prefix"]: entry["reason"] for entry in j["skip"]}


if __name__ == "__main__":
    BiolinkAligner.cli()
