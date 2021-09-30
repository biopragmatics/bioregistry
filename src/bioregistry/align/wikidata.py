# -*- coding: utf-8 -*-

"""Align Wikidata with the Bioregistry."""

from typing import Sequence

from bioregistry.align.utils import Aligner
from bioregistry.external.wikidata import get_wikidata

__all__ = [
    "WikidataAligner",
]


# Unlike the other aligners, the wikidata one doesn't really do the job of making the alignment.
# It's more of a stand-in and curation sheet generator right now.


class WikidataAligner(Aligner):
    """Aligner for Wikidata properties."""

    key = "wikidata"
    getter = get_wikidata
    curation_header = ("miriam", "databaseMiriam", "name", "database", "databaseLabel")

    def get_curation_row(self, external_id, external_entry) -> Sequence[str]:
        """Prepare curation rows for unaligned Wikidata properties."""
        return [
            external_entry.get("miriam"),
            external_entry.get("database.miriam"),
            external_entry["name"],
            external_entry["database"],
            external_entry["database.label"],
        ]

    def prepare_external(self, external_id, external_entry):  # noqa:D102
        # If it's already aligned, we don't need these extra MIRIAM annotations
        external_entry.pop("miriam", None)
        external_entry.pop("database.miriam", None)
        return external_entry


if __name__ == "__main__":
    WikidataAligner.align()
