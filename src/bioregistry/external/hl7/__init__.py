# -*- coding: utf-8 -*-

"""Utilities for getting HL7 OIDs.

1. Navigate to https://www.hl7.org/oid/index.cfm?Comp_OID=2.16.840.1.113883.6.9
2. In ``OID_Type``, select 6) for external code system
3. Download CSV and copy in this directory (this might be automatable)
"""

import csv
from pathlib import Path
from typing import Mapping

__all__ = [
    "get_hl7",
]

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


if __name__ == "__main__":
    print(len(get_hl7(force_download=True)))  # noqa:T201
