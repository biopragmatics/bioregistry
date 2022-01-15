# -*- coding: utf-8 -*-

"""Align the OBO Foundry with the Bioregistry."""

from typing import Mapping, Sequence

from bioregistry.align.utils import Aligner
from bioregistry.external.obofoundry import get_obofoundry

__all__ = [
    "OBOFoundryAligner",
]


class OBOFoundryAligner(Aligner):
    """Aligner for the OBO Foundry."""

    key = "obofoundry"
    getter = get_obofoundry
    curation_header = ("name", "description")
    include_new = True

    def get_skip(self) -> Mapping[str, str]:
        """Get the prefixes in the OBO Foundry that should be skipped."""
        return {
            "bila": "website is not longer active",
            "obo_rel": "replaced",
        }

    def get_curation_row(self, external_id, external_entry) -> Sequence[str]:
        """Prepare curation rows for unaligned BioPortal registry entries."""
        return [
            external_entry["deprecated"],
            external_entry["name"].strip(),
            external_entry.get("description", "").strip(),
        ]


if __name__ == "__main__":
    OBOFoundryAligner.cli()
