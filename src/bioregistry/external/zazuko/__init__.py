"""Download Zazuko."""

from collections.abc import Sequence
from pathlib import Path
from typing import ClassVar

import requests

from bioregistry.alignment_model import Record, dump_records, load_records
from bioregistry.constants import URI_FORMAT_KEY
from bioregistry.external.alignment_utils import Aligner

__all__ = [
    "ZazukoAligner",
    "get_zazuko",
]


DIRECTORY = Path(__file__).parent.resolve()
RAW_PATH = DIRECTORY / "raw.json"
PROCESSED_PATH = DIRECTORY / "processed.json"
URL = "https://prefix.zazuko.com/api/v1/prefixes"


def get_zazuko(*, force_download: bool = False) -> dict[str, Record]:
    """Get the Zazuko context map."""
    if PROCESSED_PATH.exists() and not force_download:
        return load_records(PROCESSED_PATH)

    data = requests.get(URL, timeout=15).json()
    rv = {
        prefix: Record(uri_format=f"{uri_prefix.strip()}$1") for prefix, uri_prefix in data.items()
    }
    dump_records(rv, PROCESSED_PATH)
    return rv


class ZazukoAligner(Aligner):
    """Aligner for Zazuko."""

    key = "zazuko"
    getter = get_zazuko
    curation_header: ClassVar[Sequence[str]] = [URI_FORMAT_KEY]


if __name__ == "__main__":
    ZazukoAligner.cli()
