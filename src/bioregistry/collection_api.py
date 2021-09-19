# -*- coding: utf-8 -*-

"""API for collections."""

from typing import Optional

from .schema import Collection
from .utils import read_collections

__all__ = [
    "get_collection",
]


def get_collection(identifier: str) -> Optional[Collection]:
    """Get the collection entry for the given identifier."""
    return read_collections().get(identifier)
