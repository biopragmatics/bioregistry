"""Utilities for interacting with data and the schema."""

from __future__ import annotations

import csv
import json
import logging
from collections import defaultdict
from collections.abc import Mapping
from functools import lru_cache
from operator import attrgetter
from pathlib import Path

from curies import Reference
from pydantic import BaseModel, Field
from typing_extensions import Literal, TypeAlias

from .constants import (
    BIOREGISTRY_PATH,
    COLLECTIONS_PATH,
    CONTEXTS_PATH,
    CURATED_MAPPINGS_PATH,
    METAREGISTRY_PATH,
)
from .schema import Collection, Context, Registry, Resource

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


class SemanticMapping(BaseModel):
    """A model representing a SSSOM semantic mapping."""

    subject: Reference = Field(..., alias="subject_id")
    predicate_modifier: Literal["Not"] | None = Field(None)
    predicate: Reference = Field(..., alias="predicate_id")
    object: Reference = Field(..., alias="object_id")
    creator: Reference = Field(..., alias="creator_id")
    mapping_justification: Reference = Field(...)
    comment: str | None = Field(None)
    issue_tracker_item: int | None = Field(
        None, description="The PR or issue associated with the change"
    )
    date: str = Field(
        ...,
        pattern="^\\d{4}-\\d{2}-\\d{2}$",
        description="The ISO-8601 date of curation in YYYY-MM-DD",
    )


def read_mismatches() -> dict[str, dict[str, set[str]]]:
    """Read the mismatches subset of curated mappings as a nested dictionary data structure."""
    mismatches: defaultdict[str, defaultdict[str, set[str]]] = defaultdict(lambda: defaultdict(set))
    for m in read_mappings():
        if m.predicate.curie == "skos:exactMatch" and m.predicate_modifier == "Not":
            mismatches[m.subject.identifier][m.object.prefix].add(m.object.identifier)
    return {k: dict(v) for k, v in mismatches.items()}


@lru_cache(maxsize=1)
def read_mappings() -> list[SemanticMapping]:
    """Read curated mappings as a nested dict data structure."""
    return _read_semantic_mappings(CURATED_MAPPINGS_PATH)


def _read_semantic_mappings(path: str | Path) -> list[SemanticMapping]:
    """Read curated mappings as a nested dict data structure."""
    with Path(path).expanduser().resolve().open() as file:
        return [
            SemanticMapping.model_validate({k: v for k, v in record.items() if v})
            for record in csv.DictReader(file, delimiter="\t")
        ]


def is_mismatch(bioregistry_prefix: str, external_metaprefix: str, external_prefix: str) -> bool:
    """Return if the triple is a mismatch."""
    return external_prefix in read_mismatches().get(bioregistry_prefix, {}).get(
        external_metaprefix, {}
    )


def write_mappings(mappings: list[SemanticMapping]) -> None:
    """Write mappings into the curated mappings file with appropriate sorting."""
    mappings = sorted(
        mappings,
        key=lambda x: (x.subject, x.object, x.predicate, x.predicate_modifier),
    )
    header = [
        "subject_id",
        "predicate_modifier",
        "predicate_id",
        "object_id",
        "creator_id",
        "mapping_justification",
        "comment",
        "issue_tracker_item",
        "date",
    ]
    with CURATED_MAPPINGS_PATH.open("w") as file:
        writer = csv.writer(file, delimiter="\t", lineterminator="\n")
        writer.writerow(header)
        writer.writerows(
            (
                mapping.subject.curie,
                mapping.predicate_modifier,
                mapping.predicate.curie,
                mapping.object.curie,
                mapping.creator.curie,
                mapping.mapping_justification.curie,
                mapping.comment,
                mapping.issue_tracker_item,
                mapping.date,
            )
            for mapping in mappings
        )


@lru_cache(maxsize=1)
def read_collections() -> Mapping[str, Collection]:
    """Read the manually curated collections."""
    return _collections_from_path(COLLECTIONS_PATH)


def _collections_from_path(path: str | Path) -> Mapping[str, Collection]:
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
            {"collections": [c.model_dump(exclude_none=True) for c in values]},
            file,
            indent=2,
            sort_keys=True,
            ensure_ascii=False,
        )


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
    """Get a mapping from contributor ORCID identifiers to collections."""
    rv = defaultdict(set)
    for collection_id, resource in collections.items():
        for author in resource.authors or []:
            rv[author.orcid].add(collection_id)
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
