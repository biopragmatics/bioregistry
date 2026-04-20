"""Utilities for interacting with data and the schema."""

from __future__ import annotations

import json
import logging
from collections import defaultdict
from collections.abc import Mapping
from functools import lru_cache
from operator import attrgetter
from pathlib import Path
from typing import TypeAlias

import sssom_pydantic
from sssom_pydantic import SemanticMapping

from .constants import (
    BIOREGISTRY_PATH,
    COLLECTIONS_PATH,
    CONTEXTS_PATH,
    CURATED_MAPPINGS_PATH,
    METAREGISTRY_PATH,
)
from .schema import Collection, Context, Registry, Resource
from .schema.struct import CollectionAnnotation

__all__ = [
    "OrcidStr",
    "SemanticMapping",
    "add_collection",
    "add_resource",
    "get_collection_mappings",
    "is_mismatch",
    "read_collections",
    "read_collections_contributions",
    "read_context_contributions",
    "read_contexts",
    "read_has_version_mappings",
    "read_mappings",
    "read_metaregistry",
    "read_mismatches",
    "read_prefix_contacts",
    "read_prefix_contributions",
    "read_prefix_reviews",
    "read_provided_by_mappings",
    "read_registry",
    "read_registry_contributions",
    "read_status_contributions",
    "registries",
    "resources",
    "write_collections",
    "write_contexts",
    "write_metaregistry",
    "write_registry",
]

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def read_metaregistry() -> Mapping[str, Registry]:
    """Read the metaregistry."""
    return _read_metaregistry(METAREGISTRY_PATH)


def _read_metaregistry(path: str | Path) -> Mapping[str, Registry]:
    with open(path, encoding="utf-8") as file:
        data = json.load(file)
    return {
        registry.prefix: registry
        for registry in (Registry(**record) for record in data["metaregistry"])
    }


def registries() -> list[Registry]:
    """Get a list of registries in the Bioregistry."""
    return sorted(read_metaregistry().values(), key=attrgetter("prefix"))


@lru_cache(maxsize=1)
def read_registry() -> Mapping[str, Resource]:
    """Read the Bioregistry as JSON."""
    return _registry_from_path(BIOREGISTRY_PATH)


def resources() -> list[Resource]:
    """Get a list of resources in the Bioregistry."""
    return sorted(read_registry().values(), key=attrgetter("prefix"))


def _registry_from_path(path: str | Path) -> Mapping[str, Resource]:
    with open(path, encoding="utf-8") as file:
        data = json.load(file)
    for prefix, value in data.items():
        value.setdefault("prefix", prefix)
    return {prefix: Resource.model_validate(value) for prefix, value in data.items()}


def add_resource(resource: Resource) -> None:
    """Add a resource to the registry.

    :param resource: A resource object to write

    :raises KeyError: if the prefix is already present in the registry
    """
    registry = dict(read_registry())
    if resource.prefix in registry:
        raise KeyError(f"Tried to add duplicate prefix to the registry: {resource.prefix}")
    registry[resource.prefix] = resource
    # Clear the cache
    read_registry.cache_clear()
    write_registry(registry)


def read_mismatches() -> dict[str, dict[str, set[str]]]:
    """Read the mismatches subset of curated mappings as a nested dictionary data structure."""
    mismatches: defaultdict[str, defaultdict[str, set[str]]] = defaultdict(lambda: defaultdict(set))
    for m in read_mappings():
        if m.predicate.curie == "skos:exactMatch" and m.predicate_modifier == "Not":
            mismatches[m.subject.identifier][m.object.prefix].add(m.object.identifier)
    return {k: dict(v) for k, v in mismatches.items()}


def read_has_version_mappings() -> dict[str, dict[str, set[str]]]:
    """Read the version mapping subset of curated mappings as a nested dictionary data structure."""
    return _read_mappings("dcterms:hasVersion")


def read_provided_by_mappings() -> dict[str, dict[str, set[str]]]:
    """Read the provider mapping subset of curated mappings as a nested dictionary data structure."""
    return _read_mappings("bioregistry.schema:0000030")


def _read_mappings(predicate_curie: str) -> dict[str, dict[str, set[str]]]:
    rv: defaultdict[str, defaultdict[str, set[str]]] = defaultdict(lambda: defaultdict(set))
    for m in read_mappings():
        if m.predicate.curie == predicate_curie:
            rv[m.subject.identifier][m.object.prefix].add(m.object.identifier)
    return {k: dict(v) for k, v in rv.items()}


@lru_cache(maxsize=1)
def read_mappings() -> list[SemanticMapping]:
    """Read curated mappings as a nested dict data structure."""
    mappings, _, _ = sssom_pydantic.read(CURATED_MAPPINGS_PATH)
    return mappings


def is_mismatch(bioregistry_prefix: str, external_metaprefix: str, external_prefix: str) -> bool:
    """Return if the triple is a mismatch."""
    return external_prefix in read_mismatches().get(bioregistry_prefix, {}).get(
        external_metaprefix, {}
    )


@lru_cache(maxsize=1)
def read_collections() -> Mapping[str, Collection]:
    """Read the manually curated collections."""
    return _collections_from_path(COLLECTIONS_PATH)


def get_collection_mappings(external_prefix: str) -> dict[str, str]:
    """Get a mapping from internal collection IDs to external ones in the given prefix."""
    return {
        collection.identifier: mapping.identifier
        for collection in read_collections().values()
        for mapping in collection.mappings or []
        if mapping.prefix == external_prefix
    }


def _collections_from_path(path: str | Path) -> dict[str, Collection]:
    with open(path, encoding="utf-8") as file:
        data = json.load(file)
    return {
        collection.identifier: collection
        for collection in (Collection(**record) for record in data["collections"])
    }


def write_collections(collections: Mapping[str, Collection], *, path: Path | None = None) -> None:
    """Write the collections."""
    values = [v for _, v in sorted(collections.items())]
    for collection in values:
        collection.resources = _lint_collection_resources(collection.resources)
    with open(path or COLLECTIONS_PATH, encoding="utf-8", mode="w") as file:
        json.dump(
            {
                "collections": [
                    c.model_dump(exclude_none=True, exclude_defaults=True, exclude_unset=True)
                    for c in values
                ]
            },
            file,
            indent=2,
            sort_keys=True,
            ensure_ascii=False,
        )


def _lint_collection_resources(
    annotations: list[str | CollectionAnnotation],
) -> list[str | CollectionAnnotation]:
    prefix_to_annotation: dict[str, str | CollectionAnnotation] = {}
    for annotation in annotations:
        if isinstance(annotation, CollectionAnnotation):
            prefix_to_annotation[annotation.prefix] = annotation
        else:
            prefix_to_annotation[annotation] = annotation
    return sorted(prefix_to_annotation.values(), key=_collection_resource_key)


def _collection_resource_key(x: str | CollectionAnnotation) -> str:
    if isinstance(x, str):
        return x
    else:
        return x.prefix


def add_collection(collection: Collection, *, path: Path | None = None) -> None:
    """Add a new collection."""
    if path is None:
        path = COLLECTIONS_PATH
    c = _collections_from_path(path)
    c[collection.identifier] = collection
    write_collections(c, path=path)


def write_registry(registry: Mapping[str, Resource], *, path: Path | None = None) -> None:
    """Write to the Bioregistry."""
    if path is None:
        path = BIOREGISTRY_PATH
    with path.open(mode="w", encoding="utf-8") as file:
        json.dump(
            {
                key: resource.model_dump(exclude_none=True, exclude={"prefix"})
                for key, resource in registry.items()
            },
            file,
            indent=2,
            sort_keys=True,
            ensure_ascii=False,
        )


def write_metaregistry(metaregistry: Mapping[str, Registry]) -> None:
    """Write to the metaregistry."""
    values = [v for _, v in sorted(metaregistry.items())]
    with open(METAREGISTRY_PATH, mode="w", encoding="utf-8") as file:
        json.dump(
            {"metaregistry": [m.model_dump(exclude_none=True) for m in values]},
            fp=file,
            indent=2,
            sort_keys=True,
            ensure_ascii=False,
        )


def write_contexts(contexts: Mapping[str, Context]) -> None:
    """Write to contexts."""
    with open(CONTEXTS_PATH, mode="w", encoding="utf-8") as file:
        json.dump(
            {key: context.model_dump(exclude_none=True) for key, context in contexts.items()},
            fp=file,
            indent=2,
            sort_keys=True,
            ensure_ascii=False,
        )


#: An ORCID string
OrcidStr: TypeAlias = str


def read_prefix_contributions(registry: Mapping[str, Resource]) -> Mapping[OrcidStr, set[str]]:
    """Get a mapping from contributor ORCID identifiers to prefixes."""
    rv = defaultdict(set)
    for prefix, resource in registry.items():
        if resource.contributor and resource.contributor.orcid:
            rv[resource.contributor.orcid].add(prefix)
        for contributor in resource.contributor_extras or []:
            if contributor.orcid:
                rv[contributor.orcid].add(prefix)
    return dict(rv)


def read_prefix_reviews(registry: Mapping[str, Resource]) -> Mapping[OrcidStr, set[str]]:
    """Get a mapping from reviewer ORCID identifiers to prefixes."""
    rv = defaultdict(set)
    for prefix, resource in registry.items():
        if resource.reviewer and resource.reviewer.orcid:
            rv[resource.reviewer.orcid].add(prefix)
        for reviewer in resource.reviewer_extras or []:
            if reviewer.orcid:
                rv[reviewer.orcid].add(prefix)
    return dict(rv)


def read_prefix_contacts(registry: Mapping[str, Resource]) -> Mapping[OrcidStr, set[str]]:
    """Get a mapping from contact ORCID identifiers to prefixes."""
    rv = defaultdict(set)
    for prefix, resource in registry.items():
        contact_orcid = resource.get_contact_orcid()
        if contact_orcid:
            rv[contact_orcid].add(prefix)

        # Add all secondary contacts' ORCIDs
        for secondary_contact in resource.contact_extras or []:
            if secondary_contact.orcid:
                rv[secondary_contact.orcid].add(prefix)

    return dict(rv)


def read_collections_contributions(
    collections: Mapping[str, Collection],
) -> Mapping[OrcidStr, set[str]]:
    """Get a mapping from contributor/maintainer ORCID identifiers to collections."""
    rv: defaultdict[OrcidStr, set[str]] = defaultdict(set)
    for collection in collections.values():
        for contributor in collection.contributors or []:
            if contributor.orcid:
                rv[contributor.orcid].add(collection.identifier)
        for maintainer in collection.maintainers or []:
            if maintainer.orcid:
                rv[maintainer.orcid].add(collection.identifier)
    return dict(rv)


def read_registry_contributions(
    metaregistry: Mapping[str, Registry],
) -> Mapping[OrcidStr, set[str]]:
    """Get a mapping from contributor ORCID identifiers to collections."""
    rv = defaultdict(set)
    for metaprefix, resource in metaregistry.items():
        if resource.contact and resource.contact.orcid:
            rv[resource.contact.orcid].add(metaprefix)
    return dict(rv)


def read_context_contributions(contexts: Mapping[str, Context]) -> Mapping[OrcidStr, set[str]]:
    """Get a mapping from contributor ORCID identifiers to contexts."""
    rv = defaultdict(set)
    for context_key, context in contexts.items():
        for maintainer in context.maintainers:
            rv[maintainer.orcid].add(context_key)
    return dict(rv)


def read_status_contributions(
    registry: Mapping[str, Resource],
) -> Mapping[OrcidStr, set[tuple[str, str]]]:
    """Get a mapping from contributor ORCID identifiers to prefixes/provider code pairs where status checks were performed."""
    rv = defaultdict(set)
    for prefix, resource in registry.items():
        for provider in resource.get_extra_providers():
            if provider.status:
                rv[provider.status.contributor].add((prefix, provider.code))
    return dict(rv)


@lru_cache(1)
def read_contexts() -> Mapping[str, Context]:
    """Get a mapping from context keys to contexts."""
    return _contexts_from_path(CONTEXTS_PATH)


def _contexts_from_path(path: str | Path) -> Mapping[str, Context]:
    with open(path, encoding="utf-8") as file:
        data = json.load(file)
    return {key: Context(**data) for key, data in data.items()}
