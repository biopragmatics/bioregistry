"""A source for the SciCrunch Registry (SCR).

The SciCrunch static data was suggested by Anita Bandrowski in
https://github.com/biopragmatics/bioregistry/issues/949#issuecomment-1747702117.
Based on the name, it was likely exported on August 24th, 2023. It can be accessed at
https://docs.google.com/spreadsheets/d/1BEPZXZsENhK7592AR83xUwbPbR2J-GVQ/edit?\
usp=sharing&ouid=107737386203376389514&rtpof=true&sd=true.
"""

import csv
from pathlib import Path
from typing import Mapping

__all__ = [
    "get_rrid",
]

HERE = Path(__file__).parent.resolve()
PATH = HERE.joinpath("input.tsv")

COLUMN_RENAMES = {"Resource_Name": "name"}
skip = {"RIN", "Resource Information Network"}


def get_rrid(force_download: bool = False) -> Mapping[str, Mapping[str, str]]:
    """Get RRIDs."""
    rv = {}
    with PATH.open() as file:
        reader = csv.DictReader(file, delimiter="\t")
        for record in reader:
            rrid_pattern = record.get("RRID_Identifier_Pattern")
            if not rrid_pattern or not rrid_pattern.startswith("RRID:"):
                continue

            prefix = rrid_pattern[len("RRID:") :].rstrip("_")
            ddd = {
                "name": record["Resource_Name"],
                "homepage": record["Resource_URL"],
                "scr": record["scr_id"][len("SCR_") :],
                # "uri_format": f"https://scicrunch.org/resolver/RRID:{prefix}_$1",
            }

            pubmeds = [
                x[len("PMID:") :]
                for x in _split(record["Defining_Citation"])
                if x.startswith("PMID:")
            ]
            if pubmeds:
                ddd["pubmeds"] = pubmeds

            keywords = sorted(set(_split(record["Keywords"])).difference(skip))
            if keywords:
                ddd["keywords"] = keywords

            abbreviation = record["Abbreviation"]
            if abbreviation and abbreviation != prefix:
                ddd["abbreviation"] = abbreviation
            twitter = record["Twitter_Handle"]
            if twitter:
                ddd["twitter"] = twitter.lstrip("@")

            # could get license
            rv[prefix] = ddd

    return rv


def _split(s: str):
    return [c.strip() for c in s.split(",")]


if __name__ == "__main__":
    print(len(get_rrid(force_download=True)))  # noqa:T201
