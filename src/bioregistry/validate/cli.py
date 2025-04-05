"""Validation command line interface.

JSON-LD Validation

1. Passes ``bioregistry validate jsonld "https://bioregistry.io/api/collection/0000002?format=context"``
1. Fails ``bioregistry validate jsonld "https://raw.githubusercontent.com/prefixcommons/prefixcommons-py/master/prefixcommons/registry/go_context.jsonld"``
"""

import json
import sys
from pathlib import Path

import click
import requests

__all__ = [
    "validate",
]


@click.group()
def validate() -> None:
    """Validate data with the Bioregistry."""


@validate.command()
@click.argument("location")
@click.option("--relax", is_flag=True)
@click.option("--context")
@click.option(
    "--use-preferred",
    is_flag=True,
    help="If true, use preferred prefixes instead of normalized ones",
)
def jsonld(location: str, relax: bool, use_preferred: bool, context: str | None) -> None:
    """Validate a JSON-LD file."""
    if location.startswith("http://") or location.startswith("https://"):
        res = requests.get(location, timeout=15)
        res.raise_for_status()
        obj = res.json()
    else:
        path = Path(location).resolve()
        if not path.is_file():
            raise ValueError
        obj = json.loads(path.read_text())

    from .utils import validate_jsonld

    messages = validate_jsonld(obj, strict=not relax, use_preferred=use_preferred, context=context)
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
