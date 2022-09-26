# -*- coding: utf-8 -*-

"""Align HL7 External Code Systems with the Bioregistry."""

from bioregistry.align.utils import Aligner
from bioregistry.external.hl7 import get_hl7

__all__ = [
    "HL7Aligner",
]


class HL7Aligner(Aligner):
    """Aligner for HL7 External Code Systems."""

    # corresponds to the metaprefix in metaregistry.json
    key = "hl7"

    # This key tells the aligner that the prefix might not be super informative for
    # lexical matching (in this case, they're OIDs, so definitely not helpful)
    # and that there's another key inside each record that might be better
    alt_key_match = "preferred_prefix"

    # This function gets the dictionary of prefix -> record. Note that it's not
    # called but only passed by reference.
    getter = get_hl7

    # This lists all of the keys inside each record to be displayed in the curation
    # sheet. Below, the
    curation_header = ("status", "preferred_prefix", "name", "homepage", "description")


if __name__ == "__main__":
    HL7Aligner.cli()
