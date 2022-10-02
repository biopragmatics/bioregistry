# -*- coding: utf-8 -*-

"""Align Registry of Research Data Repositoris (r3data) with the Bioregistry."""

from bioregistry.align.utils import Aligner
from bioregistry.external.re3data import get_re3data

__all__ = [
    "Re3dataAligner",
]


class Re3dataAligner(Aligner):
    """Aligner for the Registry of Research Data Repositoris (r3data)."""

    key = "re3data"
    alt_key_match = "name"
    getter = get_re3data
    curation_header = ("name", "homepage", "description")


if __name__ == "__main__":
    Re3dataAligner.align()
