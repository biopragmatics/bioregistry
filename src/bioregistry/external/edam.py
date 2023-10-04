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

EDAM_PARENT_IRI = "http%253A%252F%252Fedamontology.org%252Fdata_2091"


def get_edam(force_download: bool = False):
    """Get the EDAM registry."""
    if PROCESSED_PATH.exists() and not force_download:
        return json.loads(PROCESSED_PATH.read_text())

    rv = get_ols_descendants(
        ontology="edam",
        uri=EDAM_PARENT_IRI,
        force_download=force_download,
        get_identifier=_get_identifier,
    )

    PROCESSED_PATH.write_text(json.dumps(rv, indent=2, sort_keys=True))
    return rv


def _get_identifier(term, ontology: str) -> str:
    # note that this prefix doesn't match the ontology name
    return term["obo_id"][len("data:") :]


if __name__ == "__main__":
    print(len(get_edam(force_download=True)))  # noqa:T201
