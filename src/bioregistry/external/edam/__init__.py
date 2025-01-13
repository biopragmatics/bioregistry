# -*- coding: utf-8 -*-

"""Import accessions from EDAM."""

import json
from pathlib import Path
from typing import Mapping

from bioregistry.external.alignment_utils import Aligner
from bioregistry.utils import get_ols_descendants

__all__ = [
    "get_edam",
    "EDAMAligner",
]

DIRECTORY = Path(__file__).parent.resolve()
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


class EDAMAligner(Aligner):
    """Aligner for the EDAM ontology."""

    key = "edam"
    getter = get_edam
    alt_key_match = "name"
    curation_header = ("name", "description")

    def get_skip(self) -> Mapping[str, str]:
        """Get entries that should be skipped and their reasons."""
        return {
            "1164": "MIRIAM URI not relevant",
            "1175": "BioPAX ontologies aren't globally unique",
            "2582": "GO sub-hierarchy",
            "2583": "GO sub-hierarchy",
        }


if __name__ == "__main__":
    EDAMAligner.cli()
