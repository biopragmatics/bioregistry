"""Download Zazuko."""

import json
from collections.abc import Sequence
from pathlib import Path
from typing import Any, ClassVar

import requests

from bioregistry.constants import URI_FORMAT_KEY
from bioregistry.external.alignment_utils import Aligner, load_processed

__all__ = [
    "ZazukoAligner",
    "get_zazuko",
]


DIRECTORY = Path(__file__).parent.resolve()
RAW_PATH = DIRECTORY / "raw.json"
PROCESSED_PATH = DIRECTORY / "processed.json"
URL = "https://prefix.zazuko.com/api/v1/prefixes"


def get_zazuko(*, force_download: bool = False) -> dict[str, dict[str, Any]]:
    """Get the Zazuko context map."""
    if PROCESSED_PATH.exists() and not force_download:
        return load_processed(PROCESSED_PATH)

    data = requests.get(URL, timeout=15).json()
    rv = {
        prefix: {URI_FORMAT_KEY: f"{uri_prefix.strip()}$1"} for prefix, uri_prefix in data.items()
    }
    with PROCESSED_PATH.open("w") as file:
        json.dump(rv, file, indent=2, sort_keys=True)
    return rv


class ZazukoAligner(Aligner):
    """Aligner for Zazuko."""

    key = "zazuko"
    getter = get_zazuko
    curation_header: ClassVar[Sequence[str]] = [URI_FORMAT_KEY]


if __name__ == "__main__":
    ZazukoAligner.cli()
