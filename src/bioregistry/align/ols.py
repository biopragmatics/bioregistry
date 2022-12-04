# -*- coding: utf-8 -*-

"""Align the OLS with the Bioregistry."""

from typing import Mapping

from bioregistry.align.utils import Aligner
from bioregistry.external.ols import OLS_SKIP, get_ols

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
        return OLS_SKIP


if __name__ == "__main__":
    OLSAligner.cli()
