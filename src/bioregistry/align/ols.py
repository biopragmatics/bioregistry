# -*- coding: utf-8 -*-

"""Align the OLS with the Bioregistry."""

from typing import Mapping, Sequence

from bioregistry.align.utils import Aligner
from bioregistry.external.ols import get_ols

__all__ = [
    "OLSAligner",
]


class OLSAligner(Aligner):
    """Aligner for the OLS."""

    key = "ols"
    getter = get_ols
    curation_header = ("name",)
    include_new = True

    def get_skip(self) -> Mapping[str, str]:
        """Get skipped entries from OLS."""
        return {
            "co_321:root": "this is a mistake in the way OLS imports CO",
            "phi": "this is low quality and has no associated metadata",
        }

    def get_curation_row(self, external_id, external_entry) -> Sequence[str]:
        """Prepare curation rows for unaligned BioPortal registry entries."""
        return [
            external_entry["name"].strip(),
        ]


if __name__ == "__main__":
    OLSAligner.align()
