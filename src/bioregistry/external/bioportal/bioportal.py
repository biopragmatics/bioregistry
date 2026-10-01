"""Align the BioPortal with the Bioregistry."""

from collections.abc import Sequence
from typing import ClassVar

from bioregistry.external.alignment_utils import Aligner
from bioregistry.external.bioportal import (
    get_agroportal,
    get_biodivportal,
    get_bioportal,
    get_ecoportal,
)

__all__ = [
    "AgroPortalAligner",
    "BioDivPortalAligner",
    "BioPortalAligner",
    "EcoPortalAligner",
    "OntoPortalAligner",
]


class OntoPortalAligner(Aligner):
    """Aligner for OntoPortal."""

    curation_header: ClassVar[Sequence[str]] = ("name", "homepage", "description")


class BioPortalAligner(OntoPortalAligner):
    """Aligner for BioPortal."""

    key = "bioportal"
    getter = get_bioportal


class EcoPortalAligner(OntoPortalAligner):
    """Aligner for EcoPortal."""

    key = "ecoportal"
    getter = get_ecoportal


class AgroPortalAligner(OntoPortalAligner):
    """Aligner for AgroPortal."""

    key = "agroportal"
    getter = get_agroportal


class BioDivPortalAligner(OntoPortalAligner):
    """Aligner for BioDivPortal."""

    key = "biodivportal"
    getter = get_biodivportal


if __name__ == "__main__":
    BioPortalAligner.cli()
