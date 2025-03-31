"""API for collections."""

from __future__ import annotations

from .resource_manager import manager
from .schema import Collection, Context

__all__ = [
    "get_collection",
    "get_context",
]


def get_collection(identifier: str) -> Collection | None:
    """Get the collection entry for the given identifier."""
    return manager.collections.get(identifier)


def get_context(identifier: str) -> Context | None:
    """Get the context for the given identifier."""
    return manager.get_context(identifier)
