# -*- coding: utf-8 -*-

"""Linting functions."""

import click

from bioregistry.utils import (
    read_collections,
    read_metaregistry,
    updater,
    write_collections,
    write_metaregistry,
)


@updater
def sort_registry(registry):
    """Sort the registry."""
    return registry


@click.command()
def lint():
    """Run the lint commands."""
    sort_registry()
    write_collections(read_collections())
    write_metaregistry(read_metaregistry())


if __name__ == "__main__":
    lint()
