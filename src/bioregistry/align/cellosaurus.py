# -*- coding: utf-8 -*-

"""Align Cellosaurus with the Bioregistry."""

from typing import Mapping, Sequence

from bioregistry.align.utils import Aligner
from bioregistry.constants import URI_FORMAT_KEY
from bioregistry.external.cellosaurus import get_cellosaurus

__all__ = [
    "CellosaurusAligner",
]


class CellosaurusAligner(Aligner):
    """Aligner for the Cellosaurus."""

    key = "cellosaurus"
    getter = get_cellosaurus
    curation_header = ("name", "homepage", "category", URI_FORMAT_KEY)

    def get_skip(self) -> Mapping[str, str]:
        """Get the skipped Cellosaurus identifiers."""
        return {
            "CCTCC": "dead site",
            "CCLV": "stub website, URL dead",
        }

    def get_curation_row(self, external_id, external_entry) -> Sequence[str]:
        """Prepare curation rows for unaligned BioPortal registry entries."""
        return [
            external_entry["name"],
            external_entry["homepage"],
            external_entry["category"],
            external_entry.get(URI_FORMAT_KEY, ""),
        ]


if __name__ == "__main__":
    CellosaurusAligner.align()
