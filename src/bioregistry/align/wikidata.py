# -*- coding: utf-8 -*-

"""Align Wikidata with the Bioregistry."""

from typing import Mapping

from bioregistry.align.utils import Aligner
from bioregistry.external.wikidata import SKIP, get_wikidata

__all__ = [
    "WikidataAligner",
]


# Unlike the other aligners, the wikidata one doesn't really do the job of making the alignment.
# It's more of a stand-in and curation sheet generator right now.


class WikidataAligner(Aligner):
    """Aligner for Wikidata properties."""

    key = "wikidata"
    getter = get_wikidata
    curation_header = ("name", "homepage", "description", "uri_format", "example")

    def get_skip(self) -> Mapping[str, str]:
        """Get entries to skip."""
        return SKIP


if __name__ == "__main__":
    WikidataAligner.cli()
