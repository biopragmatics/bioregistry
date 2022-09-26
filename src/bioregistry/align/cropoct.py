# -*- coding: utf-8 -*-

"""Align CropOCT with the Bioregistry."""

from bioregistry.align.utils import Aligner
from bioregistry.external.cropoct import get_cropoct

__all__ = [
    "CropOCTAligner",
]


class CropOCTAligner(Aligner):
    """Aligner for CropOCT."""

    key = "cropoct"
    getter = get_cropoct
    curation_header = ["name", "homepage", "description"]


if __name__ == "__main__":
    CropOCTAligner.align()
