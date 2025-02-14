"""Download the Chemical Information Ontology registry (children of ``CHEMINF:000464``).

To convert CHEMINF from OWL to OBO Graph JSON, do the following:

.. code-block:: sh

    $ robot convert --input cheminf.owl --format json --output cheminf.json

See the OBO Foundry workflow for preparing a docker container that has ROBOT available
"""

import json
from collections.abc import Mapping
from pathlib import Path

from bioregistry.external.alignment_utils import Aligner
from bioregistry.utils import get_ols_descendants

__all__ = [
    "ChemInfAligner",
    "get_cheminf",
]

DIRECTORY = Path(__file__).parent.resolve()
PROCESSED_PATH = DIRECTORY / "processed.json"

BASE_URL = "http%253A%252F%252Fsemanticscience.org%252Fresource%252FCHEMINF_000464"
SKIP = {
    "000467": "Not enough information available on this term.",
    "000234": "PubChem Conformer isn't actually an identifier, just a part of PubChem Compound database",
    "000303": "Double mapping onto `genbank`",
}


def get_cheminf(force_download: bool = False):
    """Get the Chemical Information Ontology registry."""
    if PROCESSED_PATH.exists() and not force_download:
        with PROCESSED_PATH.open() as file:
            return json.load(file)
    rv = get_ols_descendants(ontology="cheminf", uri=BASE_URL, force_download=force_download)
    with PROCESSED_PATH.open("w") as file:
        json.dump(rv, file, indent=2, sort_keys=True)
    return rv


class ChemInfAligner(Aligner):
    """Aligner for the Chemical Information Ontology."""

    key = "cheminf"
    getter = get_cheminf
    curation_header = ("name", "description")

    def get_skip(self) -> Mapping[str, str]:
        """Get the skipped identifiers."""
        return SKIP


if __name__ == "__main__":
    ChemInfAligner.cli()
