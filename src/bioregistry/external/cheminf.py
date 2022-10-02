# -*- coding: utf-8 -*-

"""Download the Chemical Information Ontology registry (children of ``CHEMINF:000464``).

To convert CHEMINF from OWL to OBO Graph JSON, do the following:

.. code-block:: sh

    $ robot convert --input cheminf.owl --format json --output cheminf.json

See the OBO Foundry workflow for preparing a docker container that has ROBOT available
"""

import json

from bioregistry.constants import EXTERNAL
from bioregistry.utils import get_ols_descendants

__all__ = [
    "get_cheminf",
]

DIRECTORY = EXTERNAL / "cheminf"
DIRECTORY.mkdir(exist_ok=True, parents=True)
PROCESSED_PATH = DIRECTORY / "processed.json"

BASE_URL = "http%253A%252F%252Fsemanticscience.org%252Fresource%252FCHEMINF_000464"


def get_cheminf(force_download: bool = False):
    """Get the Chemical Information Ontology registry."""
    if PROCESSED_PATH.exists() and not force_download:
        with PROCESSED_PATH.open() as file:
            return json.load(file)
    rv = get_ols_descendants(ontology="cheminf", uri=BASE_URL, force_download=force_download)
    with PROCESSED_PATH.open("w") as file:
        json.dump(rv, file, indent=2, sort_keys=True)
    return rv


if __name__ == "__main__":
    print(len(get_cheminf(force_download=True)))  # noqa:T201
