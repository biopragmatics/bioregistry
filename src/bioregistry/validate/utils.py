"""Validation utilities."""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path

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


def validate_jsonld(
    obj: str | Mapping[str, Mapping[str, str]],
    *,
    strict: bool = True,
    use_preferred: bool = False,
    context: str | None | bioregistry.Context = None,
) -> list[Message]:
    """Validate a JSON-LD object."""
    if isinstance(obj, str):
        if obj.startswith("http://") or obj.startswith("https://"):
            import requests

            res = requests.get(obj, timeout=15)
            res.raise_for_status()
            obj = res.json()
        else:
            path = Path(obj).resolve()
            if not path.is_file():
                raise ValueError
            obj = json.loads(path.read_text())

    if not isinstance(obj, dict):
        raise TypeError("data is not a dictionary")
    context_inner = obj.get("@context")
    if context_inner is None:
        raise TypeError("data is missing a @context field")
    if not isinstance(context_inner, dict):
        raise TypeError(f"@context is not a dictionary: {context_inner}")
    if use_preferred:
        prefix_text = "preferred"
    else:
        prefix_text = "standard"
    messages = []

    if context is not None:
        converter = bioregistry.manager.get_converter_from_context(context)

        def _check(pp: str) -> str | None:
            return converter.standardize_prefix(pp, strict=False)

    else:

        def _check(pp: str) -> str | None:
            return bioregistry.normalize_prefix(pp, use_preferred=use_preferred)

    for prefix, _uri_prefix in context_inner.items():
        norm_prefix = _check(prefix)
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
                        "solution": f"Switch to {prefix_text} prefix: {norm_prefix}",
                        "level": "error" if strict else "warning",
                    }
                )
            )
    return messages
