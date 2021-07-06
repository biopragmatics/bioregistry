# -*- coding: utf-8 -*-

"""Align the OLS with the Bioregistry."""

from typing import Sequence

from bioregistry.align.utils import Aligner
from bioregistry.external import get_ols

__all__ = [
    "OLSAligner",
]


class OLSAligner(Aligner):
    """Aligner for the OLS."""

    key = "ols"
    getter = get_ols
    curation_header = ("name",)
    include_new = True

    def get_curation_row(self, external_id, external_entry) -> Sequence[str]:
        """Prepare curation rows for unaligned BioPortal registry entries."""
        return [
            external_entry["name"].strip(),
        ]


if __name__ == "__main__":
    OLSAligner.align()
