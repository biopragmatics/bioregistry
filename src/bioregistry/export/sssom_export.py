"""Export the Bioregistry to SSSOM."""

import click
import sssom_pydantic
from curies import NamableReference, Reference
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

    def _make_semantic_mapping(
        internal_prefix: str,
        predicate: Reference,
        external_metaprefix: str,
        external_prefix: str,
        external_name: str,
    ) -> SemanticMapping:
        return SemanticMapping(
            subject=NamableReference(
                prefix=INTERNAL_METAPREFIX,
                identifier=internal_prefix,
                name=manager.get_name(internal_prefix),
            ),
            predicate=predicate,
            object=NamableReference(
                prefix=external_metaprefix, identifier=external_prefix, name=external_name
            ),
            justification=unspecified_matching_process,
        )

    semantic_mappings = read_mappings()
    # TODO add in subject and object labels for curated mappings

    for prefix, resource in manager.registry.items():
        mappings = resource.get_mappings()
        for metaprefix, metaidentifier in mappings.items():
            semantic_mappings.append(
                _make_semantic_mapping(
                    prefix,
                    exact_match,
                    metaprefix,
                    metaidentifier,
                    resource._get_external_value(metaprefix, "name"),
                )
            )

        for appears_in_internal_prefix in manager.get_appears_in(prefix) or []:
            semantic_mappings.append(
                _make_semantic_mapping(
                    prefix,
                    APPEARS_IN_PRED,
                    INTERNAL_METAPREFIX,
                    appears_in_internal_prefix,
                    manager.get_name(appears_in_internal_prefix),
                )
            )
        for depends_on_internal_prefix in manager.get_depends_on(prefix) or []:
            semantic_mappings.append(
                _make_semantic_mapping(
                    prefix,
                    DEPENDS_ON_PRED,
                    INTERNAL_METAPREFIX,
                    depends_on_internal_prefix,
                    manager.get_name(depends_on_internal_prefix),
                )
            )

        if resource.part_of and manager.normalize_prefix(resource.part_of):
            semantic_mappings.append(
                _make_semantic_mapping(
                    prefix,
                    part_of,
                    INTERNAL_METAPREFIX,
                    resource.part_of,
                    manager.get_name(resource.part_of),
                )
            )
        if resource.provides:
            semantic_mappings.append(
                _make_semantic_mapping(
                    prefix,
                    PROVIDES_PRED,
                    INTERNAL_METAPREFIX,
                    resource.provides,
                    manager.get_name(resource.provides),
                )
            )
        if resource.has_canonical:
            semantic_mappings.append(
                _make_semantic_mapping(
                    prefix,
                    HAS_CANONICAL_PRED,
                    INTERNAL_METAPREFIX,
                    resource.has_canonical,
                    manager.get_name(resource.has_canonical),
                )
            )

    metadata = MappingSetRecord.model_validate(SSSOM_METADATA)
    sssom_pydantic.write(
        semantic_mappings,
        SSSOM_PATH,
        metadata=metadata,
        converter=converter,
        sort=True,
    )


if __name__ == "__main__":
    export_sssom()
