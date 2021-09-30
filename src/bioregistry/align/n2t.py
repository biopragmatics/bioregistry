# -*- coding: utf-8 -*-

"""Align N2T with the Bioregistry."""

from typing import Mapping, Sequence

from bioregistry.align.utils import Aligner
from bioregistry.external import get_n2t


class N2TAligner(Aligner):
    """Aligner for the N2T."""

    key = "n2t"
    getter = get_n2t
    curation_header = ("name", "homepage", "description")

    def get_skip(self) -> Mapping[str, str]:  # noqa:D102
        return {
            "zzztestprefix": "test prefix should not be considered",
        }

    def get_curation_row(self, external_id, external_entry) -> Sequence[str]:
        """Prepare curation rows for unaligned BioPortal registry entries."""
        return [
            external_entry["name"].strip(),
            external_entry.get("homepage", "").strip(),
            external_entry.get("description", "").strip(),
        ]


if __name__ == "__main__":
    N2TAligner.align()
