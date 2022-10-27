# -*- coding: utf-8 -*-

"""Align the BARTOC with the Bioregistry."""

import json
from typing import Any, Dict, Mapping, Sequence

from bioregistry.align.utils import Aligner
from bioregistry.external.bartoc import get_bartoc

__all__ = [
    "BartocAligner",
]


class BartocAligner(Aligner):
    """Aligner for BARTOC."""

    key = "bartoc"
    getter = get_bartoc
    curation_header = ["homepage", "description"]


if __name__ == "__main__":
    BartocAligner.align()
