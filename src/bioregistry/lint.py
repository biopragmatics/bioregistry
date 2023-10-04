# -*- coding: utf-8 -*-

"""Linting functions."""

import click

from bioregistry.schema_utils import (
    read_collections,
    read_contexts,
    read_metaregistry,
    read_mismatches,
    read_registry,
    write_collections,
    write_contexts,
    write_metaregistry,
    write_mismatches,
    write_registry,
)


@click.command()
def lint():
    """Run the lint commands."""
    registry = read_registry()
    for resource in registry.values():
        if resource.synonyms:
            resource.synonyms = sorted(set(resource.synonyms))
        if resource.keywords:
            resource.keywords = sorted({k.lower() for k in resource.keywords})
    write_registry(registry)
    collections = read_collections()
    for collection in collections.values():
        collection.resources = sorted(set(collection.resources))
    write_collections(collections)
    write_metaregistry(read_metaregistry())
    write_contexts(read_contexts())
    write_mismatches(read_mismatches())


if __name__ == "__main__":
    lint()
