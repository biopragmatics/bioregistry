# -*- coding: utf-8 -*-

"""Align TogoID with the Bioregistry."""

from bioregistry.align.utils import Aligner
from bioregistry.external.togoid import get_togoid

__all__ = [
    "TogoIDAligner",
]


class TogoIDAligner(Aligner):
    """Aligner for TogoID."""

    key = "togoid"
    getter = get_togoid
    curation_header = ("name", "uri_format")


if __name__ == "__main__":
    TogoIDAligner.cli()
