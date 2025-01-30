"""Utilities for getting HL7 OIDs.

1. Navigate to https://www.hl7.org/oid/index.cfm?Comp_OID=2.16.840.1.113883.6.9
2. In ``OID_Type``, select 6) for external code system
3. Download CSV and copy in this directory (this might be automatable)
"""

import csv
from collections.abc import Mapping
from pathlib import Path

__all__ = [
    "HL7Aligner",
    "get_hl7",
]

from bioregistry.external.alignment_utils import Aligner

HERE = Path(__file__).parent.resolve()
DATA = HERE.joinpath("OID_Report.csv")

COLUMNS = {
    "Comp_OID": "prefix",
    "Symbolic_name": "preferred_prefix",
    "CodingSystemName": "name",
    "assignment_status": "status",
    "Resp_body_URL": "homepage",
    "Resp_body_name": "organization",
    "Object_description": "description",
}


def get_hl7(force_download: bool = False) -> Mapping[str, Mapping[str, str]]:
    """Get HL7 OIDs."""
    rv = {}
    with DATA.open() as file:
        reader = csv.reader(file)
        header = next(reader)
        for row in reader:
            row_dict = dict(zip(header, row))
            record = {COLUMNS[k]: v for k, v in row_dict.items() if k in COLUMNS and v}
            rv[record.pop("prefix")] = record
    return rv


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
