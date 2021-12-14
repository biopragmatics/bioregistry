# -*- coding: utf-8 -*-

"""Export the Bioregistry to SSSOM."""

import csv
import logging
from collections import namedtuple

import click
import yaml

import bioregistry
from bioregistry.constants import SSSOM_METADATA_PATH, SSSOM_PATH

__all__ = [
    "export_sssom",
]

logger = logging.getLogger(__name__)

Row = namedtuple("Row", "subject_id predicate_id object_id match_type")


def _get_curie_map():
    rv = {}
    for metaprefix, metaresource in bioregistry.read_metaregistry().items():
        if not metaresource.provider_uri_format or not metaresource.provider_uri_format.endswith(
            "$1"
        ):
            continue
        uri_prefix = metaresource.provider_uri_format.rstrip("$1")
        if metaresource.bioregistry_prefix:
            rv[metaresource.bioregistry_prefix] = uri_prefix
        elif metaprefix in bioregistry.read_registry() and not metaresource.bioregistry_prefix:
            # FIXME enforce all entries have corresponding bioregistry entry
            logger.debug("issue with overlap", metaprefix)
            continue
        else:
            rv[metaprefix] = uri_prefix
    return rv


CURIE_MAP = _get_curie_map()
del _get_curie_map

METADATA = {
    "license": "https://creativecommons.org/publicdomain/zero/1.0/",
    "mapping_provider": "https://github.com/biopragmatics/bioregistry",
    "mapping_set_group": "bioregistry",
    "mapping_set_id": "bioregistry",
    "mapping_set_title": "Bioregistry",
    "curie_map": CURIE_MAP,
}


@click.command()
def export_sssom():
    """Export the meta-registry as SSSOM."""
    rows = []
    for prefix, resource in bioregistry.read_registry().items():
        mappings = resource.get_mappings()
        for metaprefix, metaidentifier in mappings.items():
            if metaprefix not in CURIE_MAP:
                continue
            rows.append(_make_row("bioregistry", prefix, metaprefix, metaidentifier))
    with SSSOM_PATH.open("w") as file:
        writer = csv.writer(file, delimiter="\t")
        writer.writerow(Row._fields)
        writer.writerows(rows)
    with SSSOM_METADATA_PATH.open("w") as file:
        yaml.safe_dump(METADATA, file)


def _make_row(mp1: str, mi1: str, mp2: str, mi2: str) -> Row:
    return Row(
        subject_id=f"{mp1}:{mi1}",
        predicate_id="skos:exactMatch",
        object_id=f"{mp2}:{mi2}",
        match_type="sssom:HumanCurated",
    )


if __name__ == "__main__":
    export_sssom()
