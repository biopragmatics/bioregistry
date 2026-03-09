"""Export the Bioregistry to SSSOM."""

import csv
from collections import namedtuple

import click
import yaml
from curies import Reference, ReferenceTuple
from curies.vocabulary import exact_match, manual_mapping_curation, part_of

from ..constants import (
    APPEARS_IN_PRED,
    DEPENDS_ON_PRED,
    HAS_CANONICAL_PRED,
    INTERNAL_METAPREFIX,
    PROVIDES_PRED,
    SSSOM_METADATA,
    SSSOM_METADATA_PATH,
    SSSOM_PATH,
)
from ..parse_iri import normalize_prefix
from ..resolve import get_appears_in, get_depends_on
from ..resource_manager import manager
from ..schema_utils import read_registry
from ..utils import curie_to_str

__all__ = [
    "export_sssom",
]

Row = namedtuple("Row", "subject_id predicate_id object_id mapping_justification")


@click.command()
def export_sssom() -> None:
    """Export the meta-registry as SSSOM."""
    internal_prefix_map = manager.get_internal_prefix_map()

    rows = []
    for prefix, resource in read_registry().items():
        mappings = resource.get_mappings()
        for metaprefix, metaidentifier in mappings.items():
            if metaprefix not in internal_prefix_map:
                continue
            rows.append(_make_row(prefix, exact_match, metaprefix, metaidentifier))
        for appears_in_internal_prefix in get_appears_in(prefix) or []:
            rows.append(
                _make_row(
                    prefix,
                    APPEARS_IN_PRED,
                    INTERNAL_METAPREFIX,
                    appears_in_internal_prefix,
                )
            )
        for depends_on_internal_prefix in get_depends_on(prefix) or []:
            rows.append(
                _make_row(
                    prefix,
                    DEPENDS_ON_PRED,
                    INTERNAL_METAPREFIX,
                    depends_on_internal_prefix,
                )
            )
        if resource.part_of and normalize_prefix(resource.part_of):
            rows.append(_make_row(prefix, part_of, INTERNAL_METAPREFIX, resource.part_of))
        if resource.provides:
            rows.append(
                _make_row(
                    prefix,
                    PROVIDES_PRED,
                    INTERNAL_METAPREFIX,
                    resource.provides,
                )
            )
        if resource.has_canonical:
            rows.append(
                _make_row(
                    prefix,
                    HAS_CANONICAL_PRED,
                    INTERNAL_METAPREFIX,
                    resource.has_canonical,
                )
            )

    with SSSOM_PATH.open("w") as file:
        writer = csv.writer(file, delimiter="\t")
        writer.writerow(Row._fields)
        writer.writerows(rows)
    with SSSOM_METADATA_PATH.open("w") as file:
        yaml.safe_dump({**SSSOM_METADATA, "curie_map": internal_prefix_map}, file)


def _make_row(
    internal_prefix: str,
    relation: Reference | ReferenceTuple,
    external_metaprefix: str,
    external_prefix: str,
) -> Row:
    return Row(
        subject_id=curie_to_str(INTERNAL_METAPREFIX, internal_prefix),
        predicate_id=relation.curie,
        object_id=curie_to_str(external_metaprefix, external_prefix),
        mapping_justification=manual_mapping_curation.curie,
    )


if __name__ == "__main__":
    export_sssom()
