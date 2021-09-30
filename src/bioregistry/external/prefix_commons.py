# -*- coding: utf-8 -*-

"""Download Prefix Commons."""

import json

from pystow.utils import download

from bioregistry.data import EXTERNAL

__all__ = [
    "get_prefix_commons",
]

DIRECTORY = EXTERNAL / "prefixcommons"
DIRECTORY.mkdir(exist_ok=True, parents=True)
RAW_PATH = DIRECTORY / "raw.json"
PROCESSED_PATH = DIRECTORY / "processed.json"
URL = "https://raw.githubusercontent.com/prefixcommons/biocontext/master/registry/commons_context.jsonld"


# FIXME this isn't the real prefix commons
def get_prefix_commons(force_download: bool = False):
    """Get Prefix Commons."""
    if PROCESSED_PATH.exists() and not force_download:
        with PROCESSED_PATH.open() as file:
            return json.load(file)
    download(url=URL, path=RAW_PATH, force=True)
    with RAW_PATH.open() as file:
        data = json.load(file)
    rv = {prefix: {"formatter": f"{url}$1"} for prefix, url in data["@context"].items()}
    with PROCESSED_PATH.open("w") as file:
        json.dump(rv, file, indent=2, sort_keys=True)
    return rv


if __name__ == "__main__":
    get_prefix_commons(force_download=True)
