# -*- coding: utf-8 -*-

"""Align the BioPortal with the Bioregistry."""

from typing import Any, Dict, Sequence

from bioregistry.align.utils import Aligner
from bioregistry.external.bioportal import get_bioportal

__all__ = [
    "BioPortalAligner",
]


class BioPortalAligner(Aligner):
    """Aligner for BioPortal."""

    key = "bioportal"
    getter = get_bioportal
    curation_header = ("name",)

    def prepare_external(self, external_id, external_entry) -> Dict[str, Any]:
        """Prepare BioPortal data to be added to the Bioregistry for each BioPortal registry entry."""
        return {
            "name": external_entry["name"].strip(),
        }

    def get_curation_row(self, external_id, external_entry) -> Sequence[str]:
        """Prepare curation rows for unaligned BioPortal registry entries."""
        return [
            external_entry["name"].strip(),
        ]


if __name__ == "__main__":
    BioPortalAligner.align()
