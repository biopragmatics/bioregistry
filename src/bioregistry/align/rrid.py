# -*- coding: utf-8 -*-

"""Align RRID with the Bioregistry."""

from bioregistry.align.utils import Aligner
from bioregistry.external.scicrunch import get_rrid

__all__ = [
    "RRIDAligner",
]


class RRIDAligner(Aligner):
    """Aligner for the RRID."""

    key = "rrid"
    getter = get_rrid
    alt_key_match = "abbreviation"
    curation_header = ("name",)


if __name__ == "__main__":
    RRIDAligner.cli()
