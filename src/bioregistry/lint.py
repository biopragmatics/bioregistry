# -*- coding: utf-8 -*-

"""Linting functions."""

import click

from bioregistry.schema_utils import (
    read_collections,
    read_contexts,
    read_metaregistry,
    read_registry,
    write_collections,
    write_contexts,
    write_metaregistry,
    write_registry,
)


@click.command()
def lint():
    """Run the lint commands."""
    registry = read_registry()
    for resource in registry.values():
        if resource.synonyms:
            resource.synonyms = sorted(resource.synonyms)
    write_registry(registry)
    write_collections(read_collections())
    write_metaregistry(read_metaregistry())
    write_contexts(read_contexts())


if __name__ == "__main__":
    lint()
