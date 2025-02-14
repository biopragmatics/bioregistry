"""Script for adding examples automatically."""

import random
import urllib.error
from typing import Optional

import click
import pyobo
import pyobo.getters

from bioregistry import read_registry, write_registry


def main():
    """Add examples to the bioregistry from OBO/OLS."""
    registry = read_registry()
    for prefix, entry in registry.items():
        # if 'pattern' not in entry:  # TODO remove this later
        #     continue
        if "example" in entry:
            continue
        example = _get_example(prefix)
        if example is not None:
            entry["example"] = example
    write_registry(registry)


def _get_example(prefix: str) -> Optional[str]:
    if prefix in {"gaz", "bila", "pubchem.compound"}:
        return None
    if prefix in pyobo.getters.SKIP:
        return None
    try:
        x = pyobo.get_id_name_mapping(prefix)
    except (pyobo.getters.NoBuild, ValueError, urllib.error.URLError):
        return None
    if not x:
        return None
    x = list(x)
    try:
        rv = x[random.randint(0, len(x))]  # noqa:S311
    except IndexError:
        click.echo(f"failed {prefix} {x}")
        return None
    else:
        click.echo(f"adding {prefix} {rv}")
        return rv


if __name__ == "__main__":
    main()
