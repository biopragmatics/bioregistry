"""Utilities for getting HL7 OIDs.

1. Navigate to https://www.hl7.org/oid/index.cfm?Comp_OID=2.16.840.1.113883.6.9
2. In ``OID_Type``, select 6) for external code system
3. Download CSV and copy in this directory (this might be automatable)
"""

import csv
from collections.abc import Sequence
from pathlib import Path
from typing import Any, ClassVar

from bioregistry.alignment_model import Record, Status, dump_records, load_processed, make_record
from bioregistry.external.alignment_utils import Aligner, adapter

__all__ = [
    "HL7Aligner",
    "get_hl7",
]

HERE = Path(__file__).parent.resolve()
RAW_PATH = HERE.joinpath("OID_Report.csv")
PROCESSED_PATH = HERE.joinpath("processed.json")
COLUMNS = {
    "Comp_OID": "prefix",
    "Symbolic_name": "preferred_prefix",
    "CodingSystemName": "name",
    "assignment_status": "status",
    "Resp_body_URL": "homepage",
    "Resp_body_name": "organization",
    "Object_description": "description",
}


@adapter
def get_hl7(*, force_download: bool = False, force_process: bool = False) -> dict[str, Record]:
    """Get HL7 OIDs."""
    if PROCESSED_PATH.exists() and not force_download and not force_process:
        return load_processed(PROCESSED_PATH)
    rv = process_hl7(RAW_PATH)
    dump_records(rv, PROCESSED_PATH)
    return rv


def process_hl7(path: Path) -> dict[str, Record]:
    """Process HL7."""
    rv = {}
    with path.open() as file:
        reader = csv.reader(file)
        header = next(reader)
        for row in reader:
            row_dict = dict(zip(header, row, strict=False))
            record: dict[str, Any] = {
                COLUMNS[k]: v for k, v in row_dict.items() if k in COLUMNS and v
            }
            match record.pop("status"):
                case "Complete" | "Pending" | "Edited":
                    record["status"] = Status.active
                case "Retired" | "retired":
                    record["status"] = Status.inactive
                case "Deprecated" | "Obsolete":
                    record["status"] = Status.deprecated
                case "Rejected":
                    pass  # what to do?
            if organization := record.pop("organization", None):
                record.setdefault("extras", {})["organization"] = organization
            rv[record.pop("prefix")] = make_record(record)
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

    # This lists all keys inside each record to be displayed in the curation
    # sheet. Below, the
    curation_header: ClassVar[Sequence[str]] = (
        "preferred_prefix",
        "name",
        "homepage",
        "description",
    )


if __name__ == "__main__":
    HL7Aligner.cli()
