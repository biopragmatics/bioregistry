# -*- coding: utf-8 -*-

"""Align LOV with the Bioregistry."""

from bioregistry.align.utils import Aligner
from bioregistry.external.lov import get_lov

__all__ = [
    "LOVAligner",
]


class LOVAligner(Aligner):
    """Aligner for LOV."""

    key = "lov"
    getter = get_lov
    curation_header = ("name", "homepage", "uri_prefix")


if __name__ == "__main__":
    LOVAligner.cli()
