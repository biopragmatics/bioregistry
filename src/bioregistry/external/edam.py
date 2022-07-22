# -*- coding: utf-8 -*-

"""Import accessions from EDAM."""

import json

from bioregistry.constants import EXTERNAL
from bioregistry.utils import get_ols_descendants

__all__ = [
    "get_edam",
]

DIRECTORY = EXTERNAL / "edam"
DIRECTORY.mkdir(exist_ok=True, parents=True)
PROCESSED_PATH = DIRECTORY / "processed.json"

EDAM_PARENT_IRI = "http%3A%2F%2Fedamontology.org%2Fdata_2836"


def get_edam(force_download: bool = False):
    """Get the EDAM registry."""
    if PROCESSED_PATH.exists() and not force_download:
        return json.loads(PROCESSED_PATH.read_text())

    rv = get_ols_descendants(ontology="edam", uri=EDAM_PARENT_IRI, force_download=force_download)

    PROCESSED_PATH.write_text(json.dumps(rv, file, indent=2, sort_keys=True))
    return rv


if __name__ == "__main__":
    print(len(get_edam(force_download=True)))  # noqa:T201
