# -*- coding: utf-8 -*-

"""Download Biolink."""

import json
from pathlib import Path

import yaml
from pystow.utils import download

from bioregistry.constants import URI_FORMAT_KEY, RAW_DIRECTORY

__all__ = [
    "get_biolink",
]

URL = "https://raw.githubusercontent.com/biolink/biolink-model/master/biolink-model.yaml"

DIRECTORY = Path(__file__).parent.resolve()
RAW_PATH = RAW_DIRECTORY / "biolink.yaml"
PROCESSED_PATH = DIRECTORY / "processed.json"


def get_biolink(force_download: bool = False):
    """Get Biolink."""
    if PROCESSED_PATH.exists() and not force_download:
        with PROCESSED_PATH.open() as file:
            return json.load(file)
    download(url=URL, path=RAW_PATH, force=True)
    with RAW_PATH.open() as file:
        data = yaml.safe_load(file)
    rv = {
        prefix: {URI_FORMAT_KEY: f"{uri_prefix}$1"}
        for prefix, uri_prefix in data["prefixes"].items()
    }
    with PROCESSED_PATH.open("w") as file:
        json.dump(rv, file, indent=2, sort_keys=True)
    return rv


if __name__ == "__main__":
    get_biolink(force_download=True)
