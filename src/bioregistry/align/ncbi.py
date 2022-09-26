# -*- coding: utf-8 -*-

"""Align NCBI with the Bioregistry."""

import textwrap
from typing import Sequence

from bioregistry.align.utils import Aligner
from bioregistry.external.ncbi import get_ncbi

__all__ = ["NcbiAligner"]


class NcbiAligner(Aligner):
    """Aligner for NCBI xref registry."""

    key = "ncbi"
    getter = get_ncbi
    getter_kwargs = dict(force_download=False)
    curation_header = ("name", "example", "homepage")

    def get_curation_row(self, external_id, external_entry) -> Sequence[str]:
        """Return the relevant fields from an NCBI entry for pretty-printing."""
        return [
            textwrap.shorten(external_entry["name"], 50),
            external_entry.get("example"),
            external_entry.get("homepage"),
        ]


if __name__ == "__main__":
    NcbiAligner.align()
