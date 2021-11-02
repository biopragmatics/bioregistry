# -*- coding: utf-8 -*-

"""Linting functions."""

import click

from bioregistry.utils import (
    read_collections,
    read_metaregistry,
    read_registry,
    write_collections,
    write_metaregistry,
    write_registry,
)


@click.command()
def lint():
    """Run the lint commands."""
    write_registry(read_registry())
    write_collections(read_collections())
    write_metaregistry(read_metaregistry())


if __name__ == "__main__":
    lint()
