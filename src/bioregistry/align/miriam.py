# -*- coding: utf-8 -*-

"""Align MIRIAM with the Bioregistry."""

from bioregistry.align.utils import Aligner
from bioregistry.external.miriam import get_miriam

__all__ = [
    "MiriamAligner",
]


class MiriamAligner(Aligner):
    """Aligner for the MIRIAM registry."""

    key = "miriam"
    getter = get_miriam
    curation_header = ("deprecated", "name", "description")
    include_new = True


if __name__ == "__main__":
    MiriamAligner.align()
