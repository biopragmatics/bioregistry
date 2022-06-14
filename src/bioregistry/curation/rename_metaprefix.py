"""A script for renaming a metaprefix in the Bioregistry."""

import json

import click

from bioregistry import Resource, write_registry
from bioregistry.constants import BIOREGISTRY_PATH


@click.command()
@click.argument("old_metaprefix")
@click.argument("new_metaprefix")
def main(old_metaprefix: str, new_metaprefix: str):
    """Rename a metaprefix."""
    registry = json.loads(BIOREGISTRY_PATH.read_text())
    for value in registry.values():
        if old_metaprefix in value:
            value[new_metaprefix] = value.pop(old_metaprefix)
        mappings = value.get("mappings")
        if mappings and old_metaprefix in mappings:
            mappings[new_metaprefix] = mappings.pop(old_metaprefix)

    write_registry(
        {prefix: Resource(prefix=prefix, **values) for prefix, values in registry.items()}
    )


if __name__ == "__main__":
    main()
