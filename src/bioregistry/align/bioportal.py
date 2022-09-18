# -*- coding: utf-8 -*-

"""Align the BioPortal with the Bioregistry."""

from typing import Sequence

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

    curation_header = ("name", "homepage", "description")

    def get_curation_row(self, external_id, external_entry) -> Sequence[str]:
        """Prepare curation rows for unaligned registry entries."""
        return [
            external_entry["name"].strip(),
            external_entry.get("homepage", "").strip(),
            external_entry.get("description", ""),
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
    EcoPortalAligner.align()
    AgroPortalAligner.align()
    BioPortalAligner.align()
