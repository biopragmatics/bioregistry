"""Import accessions from EDAM."""

from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import ClassVar

from bioregistry.external.alignment_utils import Aligner, build_no_raw_getter
from bioregistry.utils import get_ols_descendants

__all__ = [
    "EDAMAligner",
    "get_edam",
]

DIRECTORY = Path(__file__).parent.resolve()
PROCESSED_PATH = DIRECTORY / "processed.json"

EDAM_PARENT_IRI = "http%253A%252F%252Fedamontology.org%252Fdata_2091"

get_edam = build_no_raw_getter(
    processed_path=PROCESSED_PATH,
    func=lambda: get_ols_descendants(
        ontology="edam",
        uri=EDAM_PARENT_IRI,
        get_identifier=_get_identifier,
    ),
)


def _get_identifier(term: dict[str, str], ontology: str) -> str:
    # note that this prefix doesn't match the ontology name
    return term["obo_id"][len("EDAM_data:") :]


class EDAMAligner(Aligner):
    """Aligner for the EDAM ontology."""

    key = "edam"
    getter = get_edam
    alt_key_match = "name"
    curation_header: ClassVar[Sequence[str]] = ["name", "description"]

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
