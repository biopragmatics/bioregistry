# -*- coding: utf-8 -*-

"""Align Cellosaurus with the Bioregistry."""

from typing import Mapping, Sequence

from bioregistry.align.utils import Aligner
from bioregistry.external import get_cellosaurus

__all__ = [
    "CellosaurusAligner",
]


class CellosaurusAligner(Aligner):
    """Aligner for the Cellosaurus."""

    key = "cellosaurus"
    getter = get_cellosaurus
    curation_header = ("name", "homepage", "category", "url")

    def get_skip(self) -> Mapping[str, str]:
        """Get the skipped Cellosaurus identifiers."""
        return {
            "Biosample": "",
            "CCRID": "not in english",
            "CCTCC": "dead site",
            "CCLV": "stub website, URL dead",
        }

    def get_curation_row(self, external_id, external_entry) -> Sequence[str]:
        """Prepare curation rows for unaligned BioPortal registry entries."""
        return [
            external_entry["name"],
            external_entry["homepage"],
            external_entry["category"],
            external_entry.get("url", ""),
        ]


if __name__ == "__main__":
    CellosaurusAligner.align()
