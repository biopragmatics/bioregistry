"""A source for the SciCrunch Registry (SCR).

The SciCrunch static data was suggested by Anita Bandrowski in
https://github.com/biopragmatics/bioregistry/issues/949#issuecomment-1747702117.
Based on the name, it was likely exported on August 24th, 2023. It can be accessed at
https://docs.google.com/spreadsheets/d/1BEPZXZsENhK7592AR83xUwbPbR2J-GVQ/edit?\
usp=sharing&ouid=107737386203376389514&rtpof=true&sd=true.
"""

from pathlib import Path
from typing import Mapping
import csv

HERE = Path(__file__).parent.resolve()
PATH = HERE.joinpath("input.tsv")

COLUMN_RENAMES = {"Resource_Name": "name"}


def get_rrid(force_download: bool = False) -> Mapping[str, Mapping[str, str]]:
    """Get RRIDs."""
    rv = {}
    with PATH.open() as file:
        reader = csv.DictReader(file, delimiter="\t")
        for record in reader:
            prefix = record["prefix"]
            name = record["Resource_Name"]
            citations = record["Defining_Citation"]
            rv[prefix] = {
                "name": name,
                "citations": citations,
            }
    return rv


if __name__ == "__main__":
    print(len(get_rrid(force_download=True)))  # noqa:T201
