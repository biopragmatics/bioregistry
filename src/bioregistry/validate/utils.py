"""Validation utilities."""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Literal

from pydantic import BaseModel

import bioregistry

__all__ = [
    "Message",
    "click_write_messages",
    "validate_jsonld",
    "validate_ttl",
]


class Message(BaseModel):
    """A message."""

    prefix: str
    error: str
    solution: str | None = None
    line: int | None = None
    level: Literal["warning", "error"]


LEVEL_TO_COLOR = {
    "warning": "yellow",
    "error": "red",
}


def click_write_messages(messages: list[Message]) -> None:
    """Write messages."""
    import click

    for message in messages:
        s = ""
        if message.line:
            s += f"[line {message.line}] "

        s += f"prefix: {message.prefix} - {message.error}"

        if message.solution:
            s += " > " + message.solution

        click.secho(s, fg=LEVEL_TO_COLOR[message.level])

    errors = sum(message.level == "error" for message in messages)
    if errors:
        import sys

        click.secho(f"\nfailed with {errors:,} errors", fg="red")
        sys.exit(1)


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


def validate_ttl(url: str) -> list[Message]:
    """Validate a Turtle file."""
    import requests

    def _get_curie_prefix_from_uri_prefix(uri_prefix: str) -> str | None:
        return None

    messages = []
    with requests.get(url, stream=True, timeout=15) as res:
        for line_number, line in enumerate(res.iter_lines(decode_unicode=True), start=1):
            if not line.startswith("@"):
                break

            # skip @base, or other
            if not line.startswith("@prefix"):
                continue
            line = line.removeprefix("@prefix ")

            curie_prefix, uri_prefix = line.split(":", 1)
            uri_prefix = uri_prefix.strip().rstrip(".").strip().strip("<>")

            resource = bioregistry.get_resource(curie_prefix)
            if resource is None:
                suggestion = _get_curie_prefix_from_uri_prefix(uri_prefix)
                if suggestion:
                    messages.append(
                        Message(
                            line=line_number,
                            prefix=curie_prefix,
                            error="non-standard CURIE prefix",
                            solution=f"switch to {suggestion}",
                            level="warning",
                        )
                    )
                else:
                    messages.append(
                        Message(
                            line=line_number,
                            prefix=curie_prefix,
                            error="non-standard CURIE prefix",
                            level="error",
                        )
                    )

    return messages
