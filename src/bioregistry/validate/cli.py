"""Validation command line interface."""

from __future__ import annotations

import sys

import click

__all__ = [
    "validate",
]


@click.group()
def validate() -> None:
    """Validate data with the Bioregistry."""


@validate.command()
@click.argument("location")
@click.option("--relax", is_flag=True)
@click.option(
    "--context",
    help="The Bioregistry context, e.g., obo. If none given, uses the default Bioregistry context.",
)
@click.option(
    "--use-preferred",
    is_flag=True,
    help="If true, use preferred prefixes instead of normalized ones. If a context is given, this is disregarded.",
)
def jsonld(location: str, relax: bool, use_preferred: bool, context: str | None) -> None:
    """Validate a JSON-LD file."""
    from .utils import validate_jsonld

    messages = validate_jsonld(
        location, strict=not relax, use_preferred=use_preferred, context=context
    )
    for message in messages:
        click.secho(
            f"{message.prefix} - {message.error}", fg=LEVEL_TO_COLOR[message.level], nl=False
        )
        if message.solution:
            click.echo(" > " + message.solution)
        else:
            click.echo("")

    if any(message.level == "error" for message in messages):
        click.secho("failed", fg="red")
        sys.exit(1)


LEVEL_TO_COLOR = {
    "warning": "yellow",
    "error": "red",
}
