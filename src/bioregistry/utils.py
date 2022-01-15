# -*- coding: utf-8 -*-

"""Utilities."""

import json
import logging
import warnings
from collections import defaultdict
from dataclasses import asdict, is_dataclass
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from typing import Any, List, Mapping, Set, Union

import click
import requests
from pydantic import BaseModel
from pydantic.json import ENCODERS_BY_TYPE

from .constants import (
    BIOREGISTRY_PATH,
    COLLECTIONS_PATH,
    METAREGISTRY_PATH,
    MISMATCH_PATH,
)
from .schema import Author, Collection, Registry, Resource

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
    return {key: Resource(**value) for key, value in data.items()}


def add_resource(prefix: str, resource: Resource) -> None:
    """Add a resource to the registry.

    :param prefix: A prefix.
    :param resource: A resource object to write
    :raises KeyError: if the prefix is already present in the registry
    """
    registry = dict(read_registry())
    if prefix in registry:
        raise KeyError("Tried to add duplicate entry to the registry")
    registry[prefix] = resource
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


def write_bioregistry(registry: Mapping[str, Resource]):
    """Write to the Bioregistry."""
    warnings.warn("use bioregistry.write_registry", DeprecationWarning)
    write_registry(registry)


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


def read_contributors() -> Mapping[str, Author]:
    """Get a mapping from contributor ORCID identifiers to author objects."""
    rv = {}
    for resource in read_registry().values():
        if resource.contributor:
            rv[resource.contributor.orcid] = resource.contributor
        if resource.reviewer:
            rv[resource.reviewer.orcid] = resource.reviewer
    for collection in read_collections().values():
        for author in collection.authors or []:
            rv[author.orcid] = author
    return rv


def read_prefix_contributions() -> Mapping[str, Set[str]]:
    """Get a mapping from contributor ORCID identifiers to prefixes."""
    rv = defaultdict(set)
    for prefix, resource in read_registry().items():
        if resource.contributor:
            rv[resource.contributor.orcid].add(prefix)
    return dict(rv)


def read_prefix_reviews() -> Mapping[str, Set[str]]:
    """Get a mapping from reviewer ORCID identifiers to prefixes."""
    rv = defaultdict(set)
    for prefix, resource in read_registry().items():
        if resource.reviewer:
            rv[resource.reviewer.orcid].add(prefix)
    return dict(rv)


def read_collections_contributions():
    """Get a mapping from contributor ORCID identifiers to collections."""
    rv = defaultdict(set)
    for collection_id, resource in read_collections().items():
        for author in resource.authors or []:
            rv[author.orcid].add(collection_id)
    return dict(rv)


def norm(s: str) -> str:
    """Normalize a string for dictionary key usage."""
    rv = s.lower()
    for x in " .-":
        rv = rv.replace(x, "")
    return rv


def secho(s, fg="cyan", bold=True, **kwargs):
    """Wrap :func:`click.secho`."""
    click.echo(
        f'[{datetime.now().strftime("%H:%M:%S")}] ' + click.style(s, fg=fg, bold=bold, **kwargs)
    )


#: Wikidata SPARQL endpoint. See https://www.wikidata.org/wiki/Wikidata:SPARQL_query_service#Interfacing
WIKIDATA_ENDPOINT = "https://query.wikidata.org/bigdata/namespace/wdq/sparql"


def query_wikidata(sparql: str) -> List[Mapping[str, Any]]:
    """Query Wikidata's sparql service.

    :param sparql: A SPARQL query string
    :return: A list of bindings
    """
    logger.debug("running query: %s", sparql)
    res = requests.get(WIKIDATA_ENDPOINT, params={"query": sparql, "format": "json"})
    res.raise_for_status()
    res_json = res.json()
    return res_json["results"]["bindings"]


def extended_encoder(obj: Any) -> Any:
    """Encode objects similarly to :func:`pydantic.json.pydantic_encoder`."""
    if isinstance(obj, BaseModel):
        return obj.dict(exclude_none=True)
    elif is_dataclass(obj):
        return asdict(obj)

    # Check the class type and its superclasses for a matching encoder
    for base in obj.__class__.__mro__[:-1]:
        try:
            encoder = ENCODERS_BY_TYPE[base]
        except KeyError:
            continue
        return encoder(obj)
    else:  # We have exited the for loop without finding a suitable encoder
        raise TypeError(f"Object of type '{obj.__class__.__name__}' is not JSON serializable")


class NormDict(dict):
    """A dictionary that supports lexical normalization of keys on setting and getting."""

    def __setitem__(self, key: str, value: str) -> None:
        """Set an item from the dictionary after lexically normalizing it."""
        norm_key = _norm(key)
        if value is None:
            raise ValueError(f"Tried to add empty value for {key}/{norm_key}")
        if norm_key in self and self[norm_key] != value:
            raise KeyError(
                f"Tried to add {norm_key}/{value} when already had {norm_key}/{self[norm_key]}"
            )
        super().__setitem__(norm_key, value)

    def __getitem__(self, item: str) -> str:
        """Get an item from the dictionary after lexically normalizing it."""
        return super().__getitem__(_norm(item))

    def __contains__(self, item) -> bool:
        """Check if an item is in the dictionary after lexically normalizing it."""
        return super().__contains__(_norm(item))

    def get(self, key: str, default=None) -> str:
        """Get an item from the dictionary after lexically normalizing it."""
        return super().get(_norm(key), default)


def _norm(s: str) -> str:
    """Normalize a string for dictionary key usage."""
    rv = s.casefold().lower()
    for x in " -_./":
        rv = rv.replace(x, "")
    return rv


def curie_to_str(prefix: str, identifier: str) -> str:
    """Combine a prefix and identifier into a CURIE string."""
    return f"{prefix}:{identifier}"
