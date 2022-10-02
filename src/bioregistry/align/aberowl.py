# -*- coding: utf-8 -*-

"""Align the AberOWL with the Bioregistry."""

from bioregistry.align.utils import Aligner
from bioregistry.external.aberowl import get_aberowl

__all__ = [
    "AberOWLAligner",
]


class AberOWLAligner(Aligner):
    """Aligner for AberOWL."""

    key = "aberowl"
    getter = get_aberowl
    curation_header = ["name", "homepage", "description"]


if __name__ == "__main__":
    AberOWLAligner.align()
