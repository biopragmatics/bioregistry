# -*- coding: utf-8 -*-

"""Utilities for interacting with data and the schema."""

import json
import logging
from collections import defaultdict
from functools import lru_cache
from operator import attrgetter
from pathlib import Path
from typing import List, Mapping, Optional, Set, Union

from .constants import (
    BIOREGISTRY_PATH,
    COLLECTIONS_PATH,
    CONTEXTS_PATH,
    METAREGISTRY_PATH,
    MISMATCH_PATH,
)
from .schema import Collection, Context, Registry, Resource
from .utils import extended_encoder

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def read_metaregistry() -> Mapping[str, Registry]:
    """Read the metaregistry."""
    return _read_metaregistry(METAREGISTRY_PATH)


def _read_metaregistry(path: Union[str, Path]) -> Mapping[str, Registry]:
    with open(path, encoding="utf-8") as file:
        data = json.load(file)
    return {
        registry.prefix: registry
        for registry in (Registry(**record) for record in data["metaregistry"])
    }


def registries() -> List[Registry]:
    """Get a list of registries in the Bioregistry."""
    return sorted(read_metaregistry().values(), key=attrgetter("prefix"))


@lru_cache(maxsize=1)
def read_registry() -> Mapping[str, Resource]:
    """Read the Bioregistry as JSON."""
    return _registry_from_path(BIOREGISTRY_PATH)


def resources() -> List[Resource]:
    """Get a list of resources in the Bioregistry."""
    return sorted(read_registry().values(), key=attrgetter("prefix"))


def _registry_from_path(path: Union[str, Path]) -> Mapping[str, Resource]:
    with open(path, encoding="utf-8") as file:
        data = json.load(file)
    for prefix, value in data.items():
        value.setdefault("prefix", prefix)
    return {prefix: Resource.parse_obj(value) for prefix, value in data.items()}


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


@lru_cache(maxsize=1)
def read_mismatches() -> Mapping[str, Mapping[str, str]]:
    """Read the mismatches as JSON."""
    with MISMATCH_PATH.open() as file:
        return json.load(file)


def is_mismatch(bioregistry_prefix: str, external_metaprefix: str, external_prefix: str) -> bool:
    """Return if the triple is a mismatch."""
    return external_prefix in read_mismatches().get(bioregistry_prefix, {}).get(
        external_metaprefix, {}
    )


def write_mismatches(mismatches: Mapping[str, Mapping[str, str]]) -> None:
    """Read the mismatches as JSON."""
    MISMATCH_PATH.write_text(
        json.dumps(
            mismatches,
            indent=2,
            sort_keys=True,
            ensure_ascii=False,
        )
    )


@lru_cache(maxsize=1)
def read_collections() -> Mapping[str, Collection]:
    """Read the manually curated collections."""
    return _collections_from_path(COLLECTIONS_PATH)


def _collections_from_path(path: Union[str, Path]) -> Mapping[str, Collection]:
    with open(path, encoding="utf-8") as file:
        data = json.load(file)
    return {
        collection.identifier: collection
        for collection in (Collection(**record) for record in data["collections"])
    }


def write_collections(collections: Mapping[str, Collection]) -> None:
    """Write the collections."""
    values = [v for _, v in sorted(collections.items())]
    for collection in values:
        collection.resources = sorted(set(collection.resources))
    with open(COLLECTIONS_PATH, encoding="utf-8", mode="w") as file:
        json.dump(
            {"collections": values},
            file,
            indent=2,
            sort_keys=True,
            ensure_ascii=False,
            default=extended_encoder,
        )


def write_registry(registry: Mapping[str, Resource], *, path: Optional[Path] = None) -> None:
    """Write to the Bioregistry."""
    if path is None:
        path = BIOREGISTRY_PATH
    with path.open(mode="w", encoding="utf-8") as file:
        json.dump(
            registry, file, indent=2, sort_keys=True, ensure_ascii=False, default=_registry_encoder
        )


def _registry_encoder(r):
    # this is necessary to make sure the prefix doesn't get duplicated
    if isinstance(r, Resource):
        return r.dict(exclude_none=True, exclude={"prefix"})
    return extended_encoder(r)


def write_metaregistry(metaregistry: Mapping[str, Registry]) -> None:
    """Write to the metaregistry."""
    values = [v for _, v in sorted(metaregistry.items())]
    with open(METAREGISTRY_PATH, mode="w", encoding="utf-8") as file:
        json.dump(
            {"metaregistry": values},
            fp=file,
            indent=2,
            sort_keys=True,
            ensure_ascii=False,
            default=extended_encoder,
        )


def write_contexts(contexts: Mapping[str, Context]) -> None:
    """Write to contexts."""
    with open(CONTEXTS_PATH, mode="w", encoding="utf-8") as file:
        json.dump(
            contexts,
            fp=file,
            indent=2,
            sort_keys=True,
            ensure_ascii=False,
            default=extended_encoder,
        )


def read_prefix_contributions(registry: Mapping[str, Resource]) -> Mapping[str, Set[str]]:
    """Get a mapping from contributor ORCID identifiers to prefixes."""
    rv = defaultdict(set)
    for prefix, resource in registry.items():
        if resource.contributor and resource.contributor.orcid:
            rv[resource.contributor.orcid].add(prefix)
        for contributor in resource.contributor_extras or []:
            if contributor.orcid:
                rv[contributor.orcid].add(prefix)
    return dict(rv)


def read_prefix_reviews(registry: Mapping[str, Resource]) -> Mapping[str, Set[str]]:
    """Get a mapping from reviewer ORCID identifiers to prefixes."""
    rv = defaultdict(set)
    for prefix, resource in registry.items():
        if resource.reviewer and resource.reviewer.orcid:
            rv[resource.reviewer.orcid].add(prefix)
    return dict(rv)


def read_prefix_contacts(registry: Mapping[str, Resource]) -> Mapping[str, Set[str]]:
    """Get a mapping from contact ORCID identifiers to prefixes."""
    rv = defaultdict(set)
    for prefix, resource in registry.items():
        contact_orcid = resource.get_contact_orcid()
        if contact_orcid:
            rv[contact_orcid].add(prefix)
    return dict(rv)


def read_collections_contributions(collections: Mapping[str, Collection]) -> Mapping[str, Set[str]]:
    """Get a mapping from contributor ORCID identifiers to collections."""
    rv = defaultdict(set)
    for collection_id, resource in collections.items():
        for author in resource.authors or []:
            rv[author.orcid].add(collection_id)
    return dict(rv)


def read_registry_contributions(metaregistry: Mapping[str, Registry]) -> Mapping[str, Set[str]]:
    """Get a mapping from contributor ORCID identifiers to collections."""
    rv = defaultdict(set)
    for metaprefix, resource in metaregistry.items():
        if resource.contact and resource.contact.orcid:
            rv[resource.contact.orcid].add(metaprefix)
    return dict(rv)


def read_context_contributions(contexts: Mapping[str, Context]) -> Mapping[str, Set[str]]:
    """Get a mapping from contributor ORCID identifiers to contexts."""
    rv = defaultdict(set)
    for context_key, context in contexts.items():
        for maintainer in context.maintainers:
            rv[maintainer.orcid].add(context_key)
    return dict(rv)


def read_contexts() -> Mapping[str, Context]:
    """Get a mapping from context keys to contexts."""
    return _contexts_from_path(CONTEXTS_PATH)


def _contexts_from_path(path: Union[str, Path]) -> Mapping[str, Context]:
    with open(path, encoding="utf-8") as file:
        data = json.load(file)
    return {key: Context(**data) for key, data in data.items()}
