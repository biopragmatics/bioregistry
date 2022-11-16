# -*- coding: utf-8 -*-

"""Align Wikidata with the Bioregistry."""

from bioregistry.align.utils import Aligner
from bioregistry.external.wikidata import get_wikidata

__all__ = [
    "WikidataAligner",
]


# Unlike the other aligners, the wikidata one doesn't really do the job of making the alignment.
# It's more of a stand-in and curation sheet generator right now.

SKIP = {
    "P3205": "is a relationship",
    "P3781": "is a relationship",
    "P4545": "is a relationship",
    "P3190": "is a relationship",
    "P4954": "is a relationship",
    "P4000": "is a relationship",
    "P3189": "is a relationship",
    "P3310": "is a relationship",
    "P3395": "is a data property",
    "P3387": "is a data property",
    "P3337": "is a data property",
    "P3485": "is a data property",
    "P3486": "is a data property",
}

class WikidataAligner(Aligner):
    """Aligner for Wikidata properties."""

    key = "wikidata"
    getter = get_wikidata
    curation_header = ("name", "homepage", "description", "uri_format", "example")


if __name__ == "__main__":
    WikidataAligner.align()
