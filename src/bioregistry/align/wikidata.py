# -*- coding: utf-8 -*-

"""Align Wikidata with the Bioregistry."""

from typing import Mapping

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
    "P10322": "is a data property",
    "P10630": "is a data property",
    "P1193": "is a data property",
    "P1603": "is a data property",
    "P2067": "is a data property",
    "P2844": "is a data property",
    "P2854": "is a data property",
    "P3487": "is a data property",
    "P3492": "is a data property",
    "P4214": "is a data property",
    "P3488": "is a data property",
    "P4250": "is a data property",
    "P574": "is a data property",
    "P7770": "is a data property",
    "P783": "is a data property",
    "P7862": "is a data property",
    "P8010": "is a data property",
    "P8011": "is a data property",
    "P8049": "is a data property",
    "P8556": "is a data property",
    "P9107": "is a data property",
    "Q112586709": "should not be annotated like a property",
    "Q111831044": "should not be annotated like a property",
}


class WikidataAligner(Aligner):
    """Aligner for Wikidata properties."""

    key = "wikidata"
    getter = get_wikidata
    curation_header = ("name", "homepage", "description", "uri_format", "example")

    def get_skip(self) -> Mapping[str, str]:
        """Get entries to skip."""
        return SKIP


if __name__ == "__main__":
    WikidataAligner.align()
