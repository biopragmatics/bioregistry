# -*- coding: utf-8 -*-

"""Utilities for Bioregistry data structures."""

from typing import Any, Mapping

from pydantic import BaseModel

__all__ = [
    "sanitize_dict",
    "sanitize_model",
    "sanitize_mapping",
]


def sanitize_dict(d):
    """Remove all keys that have none values from a dict."""
    rv = {}
    for key, value in d.items():
        if not value:
            continue
        if key == "synonyms":
            value = sorted(value)
        rv[key] = value
    return rv


def sanitize_model(base_model: BaseModel) -> Mapping[str, Any]:
    """Sanitize a single Pydantic model."""
    return sanitize_dict(base_model.dict())


def sanitize_mapping(mapping: Mapping[str, BaseModel]) -> Mapping[str, Mapping[str, Any]]:
    """Sanitize a dictionary whose values are Pydantic models."""
    return {key: sanitize_model(base_model) for key, base_model in mapping.items()}
