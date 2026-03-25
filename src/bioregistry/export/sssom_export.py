"""Export the Bioregistry to SSSOM."""

import click
import sssom_pydantic
from curies import Reference, ReferenceTuple
from curies.vocabulary import exact_match, part_of, unspecified_matching_process
from sssom_pydantic import MappingSetRecord, SemanticMapping

from ..constants import (
    APPEARS_IN_PRED,
    DEPENDS_ON_PRED,
    HAS_CANONICAL_PRED,
    INTERNAL_METAPREFIX,
    PROVIDES_PRED,
    SSSOM_METADATA,
    SSSOM_PATH,
)
from ..parse_iri import normalize_prefix
from ..resolve import get_appears_in, get_depends_on
from ..resource_manager import manager
from ..schema_utils import read_mappings, read_registry

__all__ = [
    "export_sssom",
]


@click.command()
def export_sssom() -> None:
    """Export the meta-registry as SSSOM."""
    converter = manager._get_internal_converter()

    semantic_mappings = read_mappings()
    for prefix, resource in read_registry().items():
        mappings = resource.get_mappings()
        for metaprefix, metaidentifier in mappings.items():
            metaprefix = converter.standardize_prefix(metaprefix, strict=True)
            semantic_mappings.append(
                _make_semantic_mapping(prefix, exact_match, metaprefix, metaidentifier)
            )

        for appears_in_internal_prefix in get_appears_in(prefix) or []:
            semantic_mappings.append(
                _make_semantic_mapping(
                    prefix,
                    APPEARS_IN_PRED,
                    INTERNAL_METAPREFIX,
                    appears_in_internal_prefix,
                )
            )
        for depends_on_internal_prefix in get_depends_on(prefix) or []:
            semantic_mappings.append(
                _make_semantic_mapping(
                    prefix,
                    DEPENDS_ON_PRED,
                    INTERNAL_METAPREFIX,
                    depends_on_internal_prefix,
                )
            )
        if resource.part_of and normalize_prefix(resource.part_of):
            semantic_mappings.append(
                _make_semantic_mapping(prefix, part_of, INTERNAL_METAPREFIX, resource.part_of)
            )
        if resource.provides:
            semantic_mappings.append(
                _make_semantic_mapping(
                    prefix,
                    PROVIDES_PRED,
                    INTERNAL_METAPREFIX,
                    resource.provides,
                )
            )
        if resource.has_canonical:
            semantic_mappings.append(
                _make_semantic_mapping(
                    prefix,
                    HAS_CANONICAL_PRED,
                    INTERNAL_METAPREFIX,
                    resource.has_canonical,
                )
            )

    metadata = MappingSetRecord.model_validate(SSSOM_METADATA)
    sssom_pydantic.write(
        semantic_mappings, SSSOM_PATH, metadata=metadata, converter=converter, sort=True
    )


def _make_semantic_mapping(
    internal_prefix: str,
    predicate: ReferenceTuple | Reference,
    external_metaprefix: str,
    external_prefix: str,
) -> SemanticMapping:
    return SemanticMapping(
        subject=Reference(prefix=INTERNAL_METAPREFIX, identifier=internal_prefix),
        predicate=Reference.from_curie(predicate.curie),
        object=Reference(prefix=external_metaprefix, identifier=external_prefix),
        justification=unspecified_matching_process,
    )


if __name__ == "__main__":
    export_sssom()
