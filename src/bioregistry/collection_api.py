"""API for collections."""

from __future__ import annotations

from typing import Literal, overload

from .resource_manager import manager
from .schema import Collection, Context, Resource

__all__ = [
    "get_collection",
    "get_collection_prefixes",
    "get_collection_resources",
    "get_context",
]


# docstr-coverage:excused `overload`
@overload
def get_collection(identifier: str, *, strict: Literal[True] = ...) -> Collection: ...


# docstr-coverage:excused `overload`
@overload
def get_collection(identifier: str, *, strict: Literal[False] = ...) -> Collection | None: ...


def get_collection(identifier: str, *, strict: bool = False) -> Collection | None:
    """Get the collection entry for the given identifier."""
    rv = manager.collections.get(identifier)
    if rv is not None:
        return rv
    if strict:
        raise KeyError
    return None


# docstr-coverage:excused `overload`
@overload
def get_collection_prefixes(identifier: str, *, strict: Literal[True] = ...) -> list[str]: ...


# docstr-coverage:excused `overload`
@overload
def get_collection_prefixes(
    identifier: str, *, strict: Literal[False] = ...
) -> list[str] | None: ...


def get_collection_prefixes(identifier: str, *, strict: bool = False) -> list[str] | None:
    """Get collection prefixes."""
    rv = manager.collections.get(identifier)
    if rv is not None:
        return rv.resources
    if strict:
        raise KeyError(f"no collection exists: {identifier}. try: {set(manager.collections)}")
    return None


# docstr-coverage:excused `overload`
@overload
def get_collection_resources(identifier: str, *, strict: Literal[True] = ...) -> list[Resource]: ...


# docstr-coverage:excused `overload`
@overload
def get_collection_resources(
    identifier: str, *, strict: Literal[False] = ...
) -> list[Resource] | None: ...


def get_collection_resources(identifier: str, *, strict: bool = False) -> list[Resource] | None:
    """Get collection resources."""
    rv = manager.collections.get(identifier)
    if rv is not None:
        return [manager.registry[r] for r in rv.resources]
    if strict:
        raise KeyError(f"no collection exists: {identifier}. try: {set(manager.collections)}")
    return None


def get_context(identifier: str) -> Context | None:
    """Get the context for the given identifier."""
    return manager.get_context(identifier)
