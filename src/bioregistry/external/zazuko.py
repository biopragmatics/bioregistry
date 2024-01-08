# -*- coding: utf-8 -*-

"""Download Zazuko."""

import json
from typing import Any, Mapping

import requests

from bioregistry.constants import EXTERNAL, URI_FORMAT_KEY

__all__ = [
    "get_zazuko",
]

DIRECTORY = EXTERNAL / "zazuko"
DIRECTORY.mkdir(exist_ok=True, parents=True)
RAW_PATH = DIRECTORY / "raw.json"
PROCESSED_PATH = DIRECTORY / "processed.json"
URL = "https://prefix.zazuko.com/api/v1/prefixes"


def get_zazuko(force_download: bool = False) -> Mapping[str, Mapping[str, Any]]:
    """Get the Zazuko context map."""
    if PROCESSED_PATH.exists() and not force_download:
        with PROCESSED_PATH.open() as file:
            return json.load(file)

    data = requests.get(URL).json()
    rv = {
        prefix: {URI_FORMAT_KEY: f"{uri_prefix.strip()}$1"} for prefix, uri_prefix in data.items()
    }
    with PROCESSED_PATH.open("w") as file:
        json.dump(rv, file, indent=2, sort_keys=True)
    return rv


if __name__ == "__main__":
    print(len(get_zazuko(force_download=True)))  # noqa:T201
