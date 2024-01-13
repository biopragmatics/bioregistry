# -*- coding: utf-8 -*-

"""Align Pathguide with the Bioregistry."""

from bioregistry.align.utils import Aligner
from bioregistry.external.pathguide import get_pathguide

__all__ = [
    "PathguideAligner",
]


class PathguideAligner(Aligner):
    """Aligner for the Pathguide."""

    key = "pathguide"
    alt_key_match = "abbreviation"
    getter = get_pathguide
    curation_header = ("abbreviation", "name", "homepage")


if __name__ == "__main__":
    PathguideAligner.cli()
