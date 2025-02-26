"""Utilities for Bioregistry data structures."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from pydantic import BaseModel

__all__ = [
    "sanitize_dict",
    "sanitize_mapping",
    "sanitize_model",
]


def sanitize_dict(d: dict[str, Any]) -> dict[str, Any]:
    """Remove all keys that have none values from a dict."""
    rv = {}
    for key, value in d.items():
        if not value:
            continue
        if key == "synonyms":
            value = sorted(value)
        rv[key] = value
    return rv


def sanitize_model(base_model: BaseModel, **kwargs: Any) -> Mapping[str, Any]:
    """Sanitize a single Pydantic model."""
    return sanitize_dict(base_model.model_dump(**kwargs))


def sanitize_mapping(mapping: Mapping[str, BaseModel]) -> Mapping[str, Mapping[str, Any]]:
    """Sanitize a dictionary whose values are Pydantic models."""
    return {key: sanitize_model(base_model) for key, base_model in mapping.items()}
