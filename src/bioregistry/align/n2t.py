# -*- coding: utf-8 -*-

"""Align N2T with the Bioregistry."""

from typing import Mapping

from bioregistry.align.utils import Aligner
from bioregistry.external.n2t import SKIP, get_n2t


class N2TAligner(Aligner):
    """Aligner for the N2T."""

    key = "n2t"
    getter = get_n2t
    curation_header = ("name", "homepage", "description")

    def get_skip(self) -> Mapping[str, str]:
        """Get the prefixes in N2T that should be skipped."""
        return SKIP


if __name__ == "__main__":
    N2TAligner.align()
