# -*- coding: utf-8 -*-

"""Download BioContext."""

import json
from typing import Any, Mapping

from pystow.utils import download

from bioregistry.constants import EXTERNAL, URI_FORMAT_KEY

__all__ = [
    "get_biocontext",
]

DIRECTORY = EXTERNAL / "biocontext"
DIRECTORY.mkdir(exist_ok=True, parents=True)
RAW_PATH = DIRECTORY / "raw.json"
PROCESSED_PATH = DIRECTORY / "processed.json"
URL = "https://raw.githubusercontent.com/prefixcommons/biocontext/master/registry/commons_context.jsonld"


def get_biocontext(force_download: bool = False) -> Mapping[str, Mapping[str, Any]]:
    """Get the BioContext context map.

    :param force_download: If true, forces download. If false and the file
        is already cached, reuses it.
    :returns: The biocontext data dictionary

    .. seealso:: https://github.com/prefixcommons/biocontext
    """
    if PROCESSED_PATH.exists() and not force_download:
        with PROCESSED_PATH.open() as file:
            return json.load(file)
    download(url=URL, path=RAW_PATH, force=force_download)
    with RAW_PATH.open() as file:
        data = json.load(file)
    rv = {
        prefix: {URI_FORMAT_KEY: f"{uri_prefix.strip()}$1"}
        for prefix, uri_prefix in data["@context"].items()
    }
    with PROCESSED_PATH.open("w") as file:
        json.dump(rv, file, indent=2, sort_keys=True)
    return rv


if __name__ == "__main__":
    print(len(get_biocontext(force_download=True)))  # noqa:T201
