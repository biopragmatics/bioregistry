# -*- coding: utf-8 -*-

"""Utilities for interacting with data and the schema."""

import json
import logging
from collections import defaultdict
from functools import lru_cache
from pathlib import Path
from typing import Dict, Mapping, Set, Union

from .constants import (
    BIOREGISTRY_PATH,
    COLLECTIONS_PATH,
    CONTEXTS_PATH,
    METAREGISTRY_PATH,
    MISMATCH_PATH,
)
from .schema import Attributable, Collection, Context, Registry, Resource
from .utils import extended_encoder

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def read_metaregistry() -> Mapping[str, Registry]:
    """Read the metaregistry."""
    with open(METAREGISTRY_PATH, encoding="utf-8") as file:
        data = json.load(file)
    return {
        registry.prefix: registry
        for registry in (Registry(**record) for record in data["metaregistry"])
    }


@lru_cache(maxsize=1)
def read_registry() -> Mapping[str, Resource]:
    """Read the Bioregistry as JSON."""
    return _registry_from_path(BIOREGISTRY_PATH)


def _registry_from_path(path: Union[str, Path]) -> Mapping[str, Resource]:
    with open(path, encoding="utf-8") as file:
        data = json.load(file)
    return {prefix: Resource(prefix=prefix, **value) for prefix, value in data.items()}


def add_resource(resource: Resource) -> None:
    """Add a resource to the registry.

    :param resource: A resource object to write
    :raises KeyError: if the prefix is already present in the registry
    """
    registry = dict(read_registry())
    if resource.prefix in registry:
        raise KeyError("Tried to add duplicate entry to the registry")
    registry[resource.prefix] = resource
    # Clear the cache
    read_registry.cache_clear()
    write_registry(registry)


@lru_cache(maxsize=1)
def read_mismatches() -> Mapping[str, Mapping[str, str]]:
    """Read the mismatches as JSON."""
    with MISMATCH_PATH.open() as file:
        return json.load(file)


def is_mismatch(bioregistry_prefix, external_metaprefix, external_prefix) -> bool:
    """Return if the triple is a mismatch."""
    return external_prefix in read_mismatches().get(bioregistry_prefix, {}).get(
        external_metaprefix, {}
    )


@lru_cache(maxsize=1)
def read_collections() -> Mapping[str, Collection]:
    """Read the manually curated collections."""
    with open(COLLECTIONS_PATH, encoding="utf-8") as file:
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


def write_registry(registry: Mapping[str, Resource]):
    """Write to the Bioregistry."""
    with open(BIOREGISTRY_PATH, mode="w", encoding="utf-8") as file:
        json.dump(
            registry, file, indent=2, sort_keys=True, ensure_ascii=False, default=extended_encoder
        )


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


def read_contributors() -> Mapping[str, Attributable]:
    """Get a mapping from contributor ORCID identifiers to author objects."""
    rv: Dict[str, Attributable] = {}
    for resource in read_registry().values():
        if resource.contributor and resource.contributor.orcid:
            rv[resource.contributor.orcid] = resource.contributor
        for contributor in resource.contributor_extras or []:
            if contributor.orcid:
                rv[contributor.orcid] = contributor
        if resource.reviewer and resource.reviewer.orcid:
            rv[resource.reviewer.orcid] = resource.reviewer
        contact = resource.get_contact()
        if contact and contact.orcid:
            rv[contact.orcid] = contact
    for metaresource in read_metaregistry().values():
        if metaresource.contact.orcid:
            rv[metaresource.contact.orcid] = metaresource.contact
    for collection in read_collections().values():
        for author in collection.authors or []:
            if author.orcid:
                rv[author.orcid] = author
    return rv


def read_prefix_contributions() -> Mapping[str, Set[str]]:
    """Get a mapping from contributor ORCID identifiers to prefixes."""
    rv = defaultdict(set)
    for prefix, resource in read_registry().items():
        if resource.contributor and resource.contributor.orcid:
            rv[resource.contributor.orcid].add(prefix)
        for contributor in resource.contributor_extras or []:
            if contributor.orcid:
                rv[contributor.orcid].add(prefix)
    return dict(rv)


def read_prefix_reviews() -> Mapping[str, Set[str]]:
    """Get a mapping from reviewer ORCID identifiers to prefixes."""
    rv = defaultdict(set)
    for prefix, resource in read_registry().items():
        if resource.reviewer and resource.reviewer.orcid:
            rv[resource.reviewer.orcid].add(prefix)
    return dict(rv)


def read_prefix_contacts() -> Mapping[str, Set[str]]:
    """Get a mapping from contact ORCID identifiers to prefixes."""
    rv = defaultdict(set)
    for prefix, resource in read_registry().items():
        contact_orcid = resource.get_contact_orcid()
        if contact_orcid:
            rv[contact_orcid].add(prefix)
    return dict(rv)


def read_collections_contributions() -> Mapping[str, Set[str]]:
    """Get a mapping from contributor ORCID identifiers to collections."""
    rv = defaultdict(set)
    for collection_id, resource in read_collections().items():
        for author in resource.authors or []:
            rv[author.orcid].add(collection_id)
    return dict(rv)


def read_registry_contributions() -> Mapping[str, Set[str]]:
    """Get a mapping from contributor ORCID identifiers to collections."""
    rv = defaultdict(set)
    for metaprefix, resource in read_metaregistry().items():
        if resource.contact and resource.contact.orcid:
            rv[resource.contact.orcid].add(metaprefix)
    return dict(rv)


def read_context_contributions() -> Mapping[str, Set[str]]:
    """Get a mapping from contributor ORCID identifiers to contexts."""
    rv = defaultdict(set)
    for context_key, context in read_contexts().items():
        for maintainer in context.maintainers:
            rv[maintainer.orcid].add(context_key)
    return dict(rv)


def read_contexts() -> Mapping[str, Context]:
    """Get a mapping from context keys to contexts."""
    return {
        key: Context(**data)
        for key, data in json.loads(CONTEXTS_PATH.read_text(encoding="utf-8")).items()
    }
