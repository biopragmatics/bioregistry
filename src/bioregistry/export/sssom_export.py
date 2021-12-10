# -*- coding: utf-8 -*-

"""Export the Bioregistry to SSSOM."""

from collections import namedtuple

import click
import csv
from itertools import combinations

import bioregistry
from bioregistry.constants import SSSOM_PATH

__all__ = [
    "export_sssom",
]

Row = namedtuple("Row", "subject_id predicate_id object_id match_type")


@click.command()
def export_sssom():
    """Export the meta-registry as SSSOM."""
    rows = []
    for prefix, resource in bioregistry.read_registry().items():
        mappings = resource.get_mappings()
        contributor = resource.contributor
        for metaprefix, metaidentifier in mappings.items():
            rows.append(_make_row("bioregistry", prefix, metaprefix, metaidentifier))
        # for (mp1, mi1), (mp2, mi2) in combinations(mappings.items(), 2):
        #     rows.append(_make_row(mp1, mi1, mp2, mi2))
    with SSSOM_PATH.open("w") as file:
        writer = csv.writer(file, delimiter="\t")
        writer.writerow(Row._fields)
        writer.writerows(rows)


def _make_row(mp1: str, mi1: str, mp2: str, mi2: str) -> Row:
    return Row(
        subject_id=f"{mp1}:{mi1}",
        predicate_id="skos:exactMatch",
        object_id=f"{mp2}:{mi2}",
        match_type="sssom:HumanCurated",
    )


if __name__ == '__main__':
    export_sssom()
