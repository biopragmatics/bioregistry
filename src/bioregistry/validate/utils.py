"""Validation utilities."""

from __future__ import annotations

import json
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal, cast

import click
from pydantic import BaseModel
from typing_extensions import NotRequired, TypedDict, Unpack

if TYPE_CHECKING:
    from bioregistry import Context

__all__ = [
    "Message",
    "click_write_messages",
    "validate_jsonld",
    "validate_linkml",
    "validate_ttl",
    "validate_virtuoso",
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


def click_write_messages(messages: list[Message], tablefmt: str | None) -> None:
    """Write messages."""
    if tablefmt is None:
        for message in messages:
            click.secho(_spacious_message(message))
    else:
        from tabulate import tabulate

        rows = [
            (
                message.prefix,
                f"`{message.uri_prefix}`" if tablefmt == "rst" else message.uri_prefix,
                message.error,
                message.solution or "",
            )
            for message in messages
        ]
        click.echo(
            tabulate(rows, headers=["prefix", "uri_prefix", "issue", "solution"], tablefmt=tablefmt)
        )

    errors = sum(message.level == "error" for message in messages)
    if errors:
        import sys

        click.secho(f"\nfailed with {errors:,} errors", fg="red")
        sys.exit(1)


def _spacious_message(message: Message) -> str:
    s = ""
    if message.line:
        s += f"[line {message.line}] "

    s += f"{message.prefix}: {message.uri_prefix}\n  "
    s += click.style("issue: " + message.error, fg=LEVEL_TO_COLOR[message.level])

    if message.solution:
        s += click.style("\n  suggestion: " + message.solution, fg="green")
    return s + "\n"


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


def validate_virtuoso(url: str, **kwargs: Any) -> list[Message]:
    """Validate a Virtuoso SPARQL endpoint's prefix map."""
    prefix_map = get_virtuoso_prefix_map(url)
    inputs: list[tuple[str, str, int | None]] = [(k, v, None) for k, v in prefix_map.items()]
    return _get_all_messages(inputs, **kwargs)


def validate_linkml(url: str, **kwargs: Any) -> list[Message]:
    """Validate a LinkML YAML configuration's prefix map."""
    prefix_map = get_linkml_prefix_map(url)
    inputs: list[tuple[str, str, int | None]] = [(k, v, None) for k, v in prefix_map.items()]
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

    # TODO need to implement URI prefix normalization and errors

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
                    solution = f"Switch to CURIE prefix {suggestions}, inferred from URI prefix"
                    level = "warning"
                else:
                    level = "error"
                    if len(suggestions) == 1:
                        up, cp = suggestions[0]
                        solution = f"Consider switching to the more specific CURIE/URI prefix pair {cp}: `{up}`"
                    else:
                        solution = "Consider switching one of these more specific CURIE/URI prefix pairs:\n\n"
                        for up, cp in suggestions:
                            solution += f"  {cp}: `{up}`\n"
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


def get_virtuoso_prefix_map(url: str) -> dict[str, str]:
    """Get the internal prefix map from a Virtuoso service.

    :param url: The URL for the SPARQL endpoint, for example:

        - https://nfdi4culture.de/sparql
        - https://dbpedia.org/sparql

    :returns: The prefix map returned by the Virtuoso service.
    """
    from bs4 import Tag
    from pystow.utils import get_soup

    if "nsdecl" not in url:
        url = url + "?nsdecl"

    soup = get_soup(url)
    table_body_tag = soup.find("tbody")
    if not isinstance(table_body_tag, Tag):
        raise ValueError(
            f"could not find table body tag, are you sure this is a Virtuoso "
            f"SPARQL endpoint? Error from {url}"
        )
    rv = {left.text: right.text for left, right in table_body_tag.find_all("tr")}
    return rv


def get_linkml_prefix_map(url: str) -> dict[str, str]:
    """Get the prefix map from a LinkML YAML configuration.

    :param url: The URL for the LinkML YAML configuration. Examples:

        - https://github.com/HendrikBorgelt/CatCore/raw/refs/heads/main/src/catcore/schema/catcore.yaml
        - https://github.com/mapping-commons/sssom/raw/refs/heads/master/src/sssom_schema/schema/sssom_schema.yaml

    :returns: The prefix map defined in the LinkML configuration
    """
    import requests
    import yaml

    res = requests.get(url, timeout=5)
    res.raise_for_status()
    data = yaml.safe_load(res.text)
    return cast(dict[str, str], data["prefixes"])
