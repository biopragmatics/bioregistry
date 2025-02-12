"""Export the Bioregistry to SSSOM."""

import csv
import logging
from collections import namedtuple

import click
import yaml

import bioregistry
from bioregistry import manager
from bioregistry.constants import SSSOM_METADATA_PATH, SSSOM_PATH
from bioregistry.utils import curie_to_str

__all__ = [
    "export_sssom",
]

logger = logging.getLogger(__name__)

Row = namedtuple("Row", "subject_id predicate_id object_id match_type")

CURIE_MAP = manager.get_internal_prefix_map()

METADATA = {
    "license": "https://creativecommons.org/publicdomain/zero/1.0/",
    "mapping_provider": "https://github.com/biopragmatics/bioregistry",
    "mapping_set_group": "bioregistry",
    "mapping_set_id": "bioregistry",
    "mapping_set_title": "Bioregistry",
    "curie_map": CURIE_MAP,
}


@click.command()
def export_sssom() -> None:
    """Export the meta-registry as SSSOM."""
    rows = []
    for prefix, resource in bioregistry.read_registry().items():
        mappings = resource.get_mappings()
        for metaprefix, metaidentifier in mappings.items():
            if metaprefix not in CURIE_MAP:
                continue
            rows.append(
                _make_row("bioregistry", prefix, "skos", "exactMatch", metaprefix, metaidentifier)
            )
        for appears_in in bioregistry.get_appears_in(prefix) or []:
            rows.append(
                _make_row(
                    "bioregistry",
                    prefix,
                    "bioregistry.schema",
                    "0000018",
                    "bioregistry",
                    appears_in,
                )
            )
        for depends_on in bioregistry.get_depends_on(prefix) or []:
            rows.append(
                _make_row(
                    "bioregistry",
                    prefix,
                    "bioregistry.schema",
                    "0000017",
                    "bioregistry",
                    depends_on,
                )
            )
        if resource.part_of and bioregistry.normalize_prefix(resource.part_of):
            rows.append(
                _make_row("bioregistry", prefix, "bfo", "0000050", "bioregistry", resource.part_of)
            )
        if resource.provides:
            rows.append(
                _make_row(
                    "bioregistry",
                    prefix,
                    "bioregistry.schema",
                    "0000011",
                    "bioregistry",
                    resource.provides,
                )
            )
        if resource.has_canonical:
            rows.append(
                _make_row(
                    "bioregistry",
                    prefix,
                    "bioregistry.schema",
                    "0000016",
                    "bioregistry",
                    resource.has_canonical,
                )
            )

    with SSSOM_PATH.open("w") as file:
        writer = csv.writer(file, delimiter="\t")
        writer.writerow(Row._fields)
        writer.writerows(rows)
    with SSSOM_METADATA_PATH.open("w") as file:
        yaml.safe_dump(METADATA, file)


def _make_row(mp1: str, mi1: str, rp: str, ri: str, mp2: str, mi2: str) -> Row:
    return Row(
        subject_id=curie_to_str(mp1, mi1),
        predicate_id=curie_to_str(rp, ri),
        object_id=curie_to_str(mp2, mi2),
        match_type="sssom:HumanCurated",
    )


if __name__ == "__main__":
    export_sssom()
