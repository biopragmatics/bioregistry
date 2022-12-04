# -*- coding: utf-8 -*-

"""Align the UniProt with the Bioregistry."""

from bioregistry.align.utils import Aligner
from bioregistry.constants import URI_FORMAT_KEY
from bioregistry.external.uniprot import get_uniprot

__all__ = [
    "UniProtAligner",
]


class UniProtAligner(Aligner):
    """Aligner for UniProt."""

    key = "uniprot"
    alt_key_match = "abbreviation"
    getter = get_uniprot
    curation_header = ("abbreviation", "name", URI_FORMAT_KEY, "category")


if __name__ == "__main__":
    UniProtAligner.cli()
