# -*- coding: utf-8 -*-

"""Utilities for Bioregistry data structures."""

import re
from typing import Any, Mapping

from pydantic import BaseModel

__all__ = [
    "EMAIL_RE_STR",
    "EMAIL_RE",
    "sanitize_model",
    "sanitize_mapping",
]

# not a perfect email regex, but close enough
EMAIL_RE_STR = r"^(\w|\.|\_|\-)+[@](\w|\_|\-|\.)+[.]\w{2,5}$"
EMAIL_RE = re.compile(EMAIL_RE_STR)


def sanitize_model(base_model: BaseModel) -> Mapping[str, Any]:
    """Sanitize a single Pydantic model."""
    return {key: value for key, value in base_model.dict().items() if value is not None}


def sanitize_mapping(mapping: Mapping[str, BaseModel]) -> Mapping[str, Mapping[str, Any]]:
    """Sanitize a dictionary whose values are Pydantic models."""
    return {key: sanitize_model(base_model) for key, base_model in mapping.items()}
