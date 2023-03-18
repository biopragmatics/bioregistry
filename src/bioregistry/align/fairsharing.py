# -*- coding: utf-8 -*-

"""Align FAIRsharing with the Bioregistry."""

from bioregistry.align.utils import Aligner
from bioregistry.external.fairsharing import get_fairsharing

__all__ = [
    "FairsharingAligner",
]


class FairsharingAligner(Aligner):
    """Aligner for the FAIRsharing."""

    key = "fairsharing"
    alt_key_match = "abbreviation"
    skip_deprecated = True
    getter = get_fairsharing
    curation_header = ("abbreviation", "name", "description")


if __name__ == "__main__":
    FairsharingAligner.cli()
