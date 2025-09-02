"""Validation utilities."""

from __future__ import annotations

import json
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import TYPE_CHECKING, Literal

from pydantic import BaseModel
from typing_extensions import NotRequired, TypedDict, Unpack

if TYPE_CHECKING:
    from bioregistry import Context

__all__ = [
    "Message",
    "click_write_messages",
    "validate_jsonld",
    "validate_ttl",
]


class Message(BaseModel):
    """A message."""

    prefix: str
    uri_prefix: str
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

        s += f"{message.prefix}: {message.uri_prefix}\n  {message.error}"

        if message.solution:
            s += ". " + message.solution

        click.secho(s, fg=LEVEL_TO_COLOR[message.level])

    errors = sum(message.level == "error" for message in messages)
    if errors:
        import sys

        click.secho(f"\nfailed with {errors:,} errors", fg="red")
        sys.exit(1)


class ValidateKwargs(TypedDict):
    """Keyword arguments for validators, passed to :func:`_get_all_messages`."""

    rpm: NotRequired[Mapping[str, str] | None]
    use_preferred: NotRequired[bool]
    context: NotRequired[str | Context | None]
    strict: NotRequired[bool]


def validate_jsonld(
    obj: str | Mapping[str, Mapping[str, str]], **kwargs: Unpack[ValidateKwargs]
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

    inputs: list[tuple[str, str, int | None]] = [(cp, up, None) for cp, up in context_inner.items()]

    return _get_all_messages(inputs, **kwargs)


def validate_ttl(url: str, **kwargs: Unpack[ValidateKwargs]) -> list[Message]:
    """Validate a remote Turtle file."""
    import requests

    inputs: list[tuple[str, str, int | None]] = []
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
            inputs.append((curie_prefix, uri_prefix, line_number))

    return _get_all_messages(inputs, **kwargs)


def _get_all_messages(
    inputs: list[tuple[str, str, int | None]],
    *,
    context: str | None | Context = None,
    use_preferred: bool = False,
    rpm: Mapping[str, str] | None = None,
    strict: bool = False,
) -> list[Message]:
    """Get messages for the given inputs."""
    import bioregistry

    if rpm is None:
        rpm = bioregistry.manager.get_reverse_prefix_map()

    def _get_suggestions(uri_prefix: str) -> list[tuple[str, str]] | str:
        suggies = []
        for x, y in rpm.items():
            if x.startswith(uri_prefix):
                suggies.append((x, y))
            if x == uri_prefix:
                return y
        return suggies

    _checker = _get_checker(context, use_preferred=use_preferred)

    messages: list[Message] = []
    for curie_prefix, uri_prefix, line_number in inputs:
        resource = bioregistry.get_resource(curie_prefix)
        if resource is None:
            suggestions = _get_suggestions(uri_prefix)
            if not suggestions:
                messages.append(
                    Message(
                        line=line_number,
                        prefix=curie_prefix,
                        uri_prefix=uri_prefix,
                        error="unknown CURIE prefix",
                        level="error",
                    )
                )
            else:
                if isinstance(suggestions, str):
                    solution = f"Switch to {suggestions}"
                    level = "warning"
                else:
                    level = "error"
                    if len(suggestions) == 1:
                        up, cp = suggestions[0]
                        solution = f"Consider switching to the specific CURIE/URI prefix pair `{cp}` and `{up}`"
                    else:
                        solution = "Consider switching one of these more specific CURIE/URI prefix pairs:\n\n"
                        for up, cp in suggestions:
                            solution += f"  `{cp}` and `{up}`\n"
                messages.append(
                    Message(
                        line=line_number,
                        prefix=curie_prefix,
                        uri_prefix=uri_prefix,
                        error="unknown CURIE prefix",
                        solution=solution,
                        level=level,
                    )
                )

        else:
            if message := _get_message(
                curie_prefix,
                uri_prefix,
                _checker,
                strict=strict,
                line_number=line_number,
                use_preferred=use_preferred,
            ):
                messages.append(message)

    return messages


def _get_message(
    curie_prefix: str,
    uri_prefix: str,
    _checker: Callable[[str], str | None],
    *,
    strict: bool = False,
    line_number: int | None = None,
    use_preferred: bool = False,
) -> Message | None:
    norm_prefix = _checker(curie_prefix)
    if use_preferred:
        middle = "preferred"
    else:
        middle = "standard"
    if norm_prefix is None:
        return Message(
            prefix=curie_prefix,
            uri_prefix=uri_prefix,
            error="unknown CURIE prefix",
            level="error",
            line=line_number,
        )
    elif norm_prefix != curie_prefix:
        return Message(
            prefix=curie_prefix,
            uri_prefix=uri_prefix,
            error="non-standard CURIE prefix",
            solution=f"Switch to {middle} prefix: {norm_prefix}",
            level="error" if strict else "warning",
            line=line_number,
        )
    else:
        return None


def _get_checker(
    context: str | None | Context = None, use_preferred: bool = False
) -> Callable[[str], str | None]:
    import bioregistry

    if context is not None:
        converter = bioregistry.manager.get_converter_from_context(context)

        def _check(pp: str) -> str | None:
            return converter.standardize_prefix(pp, strict=False)

    else:

        def _check(pp: str) -> str | None:
            return bioregistry.normalize_prefix(pp, use_preferred=use_preferred)

    return _check
