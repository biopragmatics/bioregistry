# -*- coding: utf-8 -*-

"""Align the BARTOC with the Bioregistry."""

from bioregistry.align.utils import Aligner
from bioregistry.external.bartoc import get_bartoc

__all__ = [
    "BartocAligner",
]


class BartocAligner(Aligner):
    """Aligner for BARTOC."""

    key = "bartoc"
    getter = get_bartoc
    alt_key_match = "abbreviation"
    curation_header = ["name", "homepage", "description"]


if __name__ == "__main__":
    BartocAligner.cli()
