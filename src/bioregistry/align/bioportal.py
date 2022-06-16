# -*- coding: utf-8 -*-

"""Align the BioPortal with the Bioregistry."""

from typing import Any, Dict, Sequence

from bioregistry.align.utils import Aligner
from bioregistry.external.bioportal import get_agroportal, get_bioportal, get_ecoportal

__all__ = [
    # Base class
    "OntoPortalAligner",
    # Concrete classes
    "BioPortalAligner",
    "AgroPortalAligner",
    "EcoPortalAligner",
]


class OntoPortalAligner(Aligner):
    """Aligner for OntoPortal."""

    curation_header = ("name",)

    def prepare_external(self, external_id, external_entry) -> Dict[str, Any]:
        """Prepare OntoPortal data to be added to the Bioregistry for each registry entry."""
        return {
            "name": external_entry["name"].strip(),
        }

    def get_curation_row(self, external_id, external_entry) -> Sequence[str]:
        """Prepare curation rows for unaligned registry entries."""
        return [
            external_entry["name"].strip(),
        ]


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


if __name__ == "__main__":
    BioPortalAligner.align()
    EcoPortalAligner.align()
    AgroPortalAligner.align()
