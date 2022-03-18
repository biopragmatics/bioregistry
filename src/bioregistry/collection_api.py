# -*- coding: utf-8 -*-

"""API for collections."""

from typing import Optional

from .schema import Collection, Context
from .utils import read_collections, read_contexts

__all__ = [
    "get_collection",
    "get_context",
]


def get_collection(identifier: str) -> Optional[Collection]:
    """Get the collection entry for the given identifier."""
    return read_collections().get(identifier)


def get_context(identifier: str) -> Optional[Context]:
    """Get the context for the given identifier."""
    return read_contexts().get(identifier)
