# -*- coding: utf-8 -*-

"""Align HL7 External Code Systems with the Bioregistry."""

from typing import Sequence

from bioregistry.align.utils import Aligner
from bioregistry.external.hl7 import get_hl7

__all__ = [
    "HL7Aligner",
]


class HL7Aligner(Aligner):
    """Aligner for HL7 External Code Systems."""

    key = "hl7"
    alt_key_match = "preferred_prefix"
    getter = get_hl7
    curation_header = ("status", "preferred_prefix", "name", "homepage", "description")

    def get_curation_row(self, external_id, external_entry) -> Sequence[str]:
        """Prepare curation rows for unaligned OID entries."""
        return [
            external_entry["status"],
            external_entry["preferred_prefix"],
            external_entry.get("name") or "",
            external_entry.get("homepage") or "",
            external_entry.get("description") or "",
        ]


if __name__ == "__main__":
    HL7Aligner.cli()
