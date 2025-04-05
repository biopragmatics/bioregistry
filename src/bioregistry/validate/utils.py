"""Validation utilities."""

from __future__ import annotations

from collections.abc import Mapping

from pydantic import BaseModel
from typing_extensions import Literal

import bioregistry

__all__ = [
    "Message",
    "validate_jsonld",
]


class Message(BaseModel):
    """A message."""

    prefix: str
    error: str
    solution: str | None = None
    level: Literal["warning", "error"]


def validate_jsonld(obj: Mapping[str, Mapping[str, str]], *, strict: bool = True) -> list[Message]:
    """Validate a JSON-LD object."""
    if not isinstance(obj, dict):
        raise TypeError("data is not a dictionary")
    context = obj.get("@context")
    if context is None:
        raise TypeError("data is missing a @context field")
    if not isinstance(context, dict):
        raise TypeError(f"@context is not a dictionary: {context}")
    messages = []
    for prefix, _uri_prefix in context.items():
        norm_prefix = bioregistry.normalize_prefix(prefix)
        if norm_prefix is None:
            messages.append(
                Message.model_validate(
                    {
                        "prefix": prefix,
                        "error": "invalid",
                        "solution": None,
                        "level": "error",
                    }
                )
            )
        elif norm_prefix != prefix:
            messages.append(
                Message.model_validate(
                    {
                        "prefix": prefix,
                        "error": "nonstandard",
                        "solution": f"Switch to standard prefix: {norm_prefix}",
                        "level": "error" if strict else "warning",
                    }
                )
            )
    return messages
