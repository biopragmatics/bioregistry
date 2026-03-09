"""Download the Chemical Information Ontology registry (children of ``CHEMINF:000464``).

To convert CHEMINF from OWL to OBO Graph JSON, do the following:

.. code-block:: sh

    $ robot convert --input cheminf.owl --format json --output cheminf.json

See the OBO Foundry workflow for preparing a docker container that has ROBOT available
"""

from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import ClassVar

from bioregistry.external.alignment_utils import Aligner, build_no_raw_getter
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

get_cheminf = build_no_raw_getter(
    processed_path=PROCESSED_PATH,
    func=lambda: get_ols_descendants(ontology="cheminf", uri=BASE_URL),
)


class ChemInfAligner(Aligner):
    """Aligner for the Chemical Information Ontology."""

    key = "cheminf"
    getter = get_cheminf
    curation_header: ClassVar[Sequence[str]] = ["name", "description"]

    def get_skip(self) -> Mapping[str, str]:
        """Get the skipped identifiers."""
        return SKIP


if __name__ == "__main__":
    ChemInfAligner.cli()
