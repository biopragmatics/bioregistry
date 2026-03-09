"""Download Zazuko."""

import json
from collections.abc import Sequence
from pathlib import Path
from typing import ClassVar

from bioregistry.alignment_model import Record
from bioregistry.constants import URI_FORMAT_KEY
from bioregistry.external.alignment_utils import Aligner, build_getter, cleanup_json

__all__ = [
    "ZazukoAligner",
    "get_zazuko",
    "parse_zazuko_raw",
]

DIRECTORY = Path(__file__).parent.resolve()
RAW_PATH = DIRECTORY / "raw.json"
PROCESSED_PATH = DIRECTORY / "processed.json"
URL = "https://prefix.zazuko.com/api/v1/prefixes"


def parse_zazuko_raw(path: Path) -> dict[str, Record]:
    """Parse Zazuko raw JSON data."""
    data = json.loads(path.read_text())
    rv = {
        prefix: Record(uri_format=f"{uri_prefix.strip()}$1") for prefix, uri_prefix in data.items()
    }
    return rv


get_zazuko = build_getter(
    processed_path=PROCESSED_PATH,
    raw_path=RAW_PATH,
    url=URL,
    func=parse_zazuko_raw,
    cleanup=cleanup_json,
)


class ZazukoAligner(Aligner):
    """Aligner for Zazuko."""

    key = "zazuko"
    getter = get_zazuko
    curation_header: ClassVar[Sequence[str]] = [URI_FORMAT_KEY]


if __name__ == "__main__":
    ZazukoAligner.cli()
