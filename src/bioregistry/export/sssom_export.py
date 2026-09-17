"""Export the Bioregistry to SSSOM."""

import click
import sssom_pydantic
from curies import NamableReference, Reference, ReferenceTuple
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
from ..resource_manager import Manager
from ..schema_utils import read_mappings

__all__ = [
    "export_sssom",
]


@click.command()
def export_sssom() -> None:
    """Export the meta-registry as SSSOM."""
    manager = Manager()
    converter = manager._get_internal_converter()

    semantic_mappings = read_mappings()
    for prefix, resource in manager.registry.items():
        mappings = resource.get_mappings()
        for metaprefix, metaidentifier in mappings.items():
            metaprefix = converter.standardize_prefix(metaprefix, strict=True)
            semantic_mappings.append(
                _make_semantic_mapping(
                    prefix,
                    exact_match,
                    metaprefix,
                    metaidentifier,
                    manager=manager,
                )
            )

        for appears_in_internal_prefix in manager.get_appears_in(prefix) or []:
            semantic_mappings.append(
                _make_semantic_mapping(
                    prefix,
                    APPEARS_IN_PRED,
                    INTERNAL_METAPREFIX,
                    appears_in_internal_prefix,
                    manager=manager,
                )
            )
        for depends_on_internal_prefix in manager.get_depends_on(prefix) or []:
            semantic_mappings.append(
                _make_semantic_mapping(
                    prefix,
                    DEPENDS_ON_PRED,
                    INTERNAL_METAPREFIX,
                    depends_on_internal_prefix,
                    manager=manager,
                )
            )

        if resource.part_of and manager.normalize_prefix(resource.part_of):
            semantic_mappings.append(
                _make_semantic_mapping(
                    prefix,
                    part_of,
                    INTERNAL_METAPREFIX,
                    resource.part_of,
                    manager=manager,
                )
            )
        if resource.provides:
            semantic_mappings.append(
                _make_semantic_mapping(
                    prefix,
                    PROVIDES_PRED,
                    INTERNAL_METAPREFIX,
                    resource.provides,
                    manager=manager,
                )
            )
        if resource.has_canonical:
            semantic_mappings.append(
                _make_semantic_mapping(
                    prefix,
                    HAS_CANONICAL_PRED,
                    INTERNAL_METAPREFIX,
                    resource.has_canonical,
                    manager=manager,
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
    manager: Manager,
) -> SemanticMapping:
    resource = manager.get_resource(internal_prefix, strict=True)
    external_name = resource._get_external_value(external_metaprefix, "name")
    return SemanticMapping(
        subject=NamableReference(
            prefix=INTERNAL_METAPREFIX,
            identifier=internal_prefix,
            name=manager.get_name(internal_prefix),
        ),
        predicate=Reference.from_curie(predicate.curie),
        object=NamableReference(
            prefix=external_metaprefix, identifier=external_prefix, name=external_name
        ),
        justification=unspecified_matching_process,
    )


if __name__ == "__main__":
    export_sssom()
