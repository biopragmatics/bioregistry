# -*- coding: utf-8 -*-

"""Align CropOCT with the Bioregistry."""

from typing import Sequence

from bioregistry.align.utils import Aligner
from bioregistry.external.cropoct import get_cropoct

__all__ = [
    "CropOCTAligner",
]


class CropOCTAligner(Aligner):
    """Aligner for CropOCT."""

    key = "cropoct"
    getter = get_cropoct
    curation_header = ["name", "homepage", "description"]

    def get_curation_row(self, external_id, external_entry) -> Sequence[str]:
        """Prepare curation rows for unaligned registry entries."""
        return [
            external_entry["name"],
            external_entry.get("homepage", ""),
            external_entry.get("description", ""),
        ]


if __name__ == "__main__":
    CropOCTAligner.align()
