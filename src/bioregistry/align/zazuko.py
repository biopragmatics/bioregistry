# -*- coding: utf-8 -*-

"""Align the Zazuko with the Bioregistry."""

from bioregistry.align.utils import Aligner
from bioregistry.constants import URI_FORMAT_KEY
from bioregistry.external.zazuko import get_zazuko

__all__ = [
    "ZazukoAligner",
]


class ZazukoAligner(Aligner):
    """Aligner for Zazukp."""

    key = "zazuko"
    getter = get_zazuko
    curation_header = [URI_FORMAT_KEY]


if __name__ == "__main__":
    ZazukoAligner.cli()
