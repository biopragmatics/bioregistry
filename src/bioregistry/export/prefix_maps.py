# -*- coding: utf-8 -*-

"""Export extended prefix maps (EPMs), JSON-LD contexts, and SHACL RDF documents.

.. seealso:: https://github.com/biopragmatics/bioregistry/pull/972
"""

import json

import click
import curies

from bioregistry.constants import (
    CONTEXT_BIOREGISTRY_PATH,
    EXPORT_CONTEXTS,
    SHACL_TURTLE_PATH,
)
from bioregistry.resource_manager import manager

REVERSE_PREFIX_MAP_PATH = EXPORT_CONTEXTS.joinpath("bioregistry.rpm.json")
EXTENDED_PREFIX_MAP_PATH = EXPORT_CONTEXTS.joinpath("bioregistry.epm.json")


@click.command()
def generate_contexts():
    """Generate various context files."""
    reverse_prefix_map = manager.get_reverse_prefix_map(include_prefixes=True, strict=False)
    REVERSE_PREFIX_MAP_PATH.write_text(json.dumps(reverse_prefix_map, indent=4, sort_keys=True))

    _context_prefix_maps()
    _collection_prefix_maps()

    converter = manager.get_converter(include_prefixes=True)
    curies.write_jsonld_context(converter, CONTEXT_BIOREGISTRY_PATH)
    curies.write_shacl(converter, SHACL_TURTLE_PATH)
    curies.write_extended_prefix_map(converter, EXTENDED_PREFIX_MAP_PATH)


def _collection_prefix_maps():
    converter = manager.get_converter()
    for collection in manager.collections.values():
        name = collection.context
        if name is None:
            continue
        path_stub = EXPORT_CONTEXTS.joinpath(name)
        subconverter = converter.get_subconverter(collection.resources)
        curies.write_jsonld_context(subconverter, path_stub.with_suffix(".context.jsonld"))
        curies.write_shacl(subconverter, path_stub.with_suffix(".context.ttl"))


def _context_prefix_maps():
    for key in manager.contexts:
        converter = manager.get_converter_from_context(key)

        stub = EXPORT_CONTEXTS.joinpath(key)
        curies.write_jsonld_context(converter, stub.with_suffix(".context.jsonld"))
        curies.write_shacl(converter, stub.with_suffix(".context.ttl"))
        curies.write_extended_prefix_map(converter, stub.with_suffix(".epm.json"))

        if key == "obo":  # Special case, maybe put this in data model
            synonyms_stub = EXPORT_CONTEXTS.joinpath(f"{key}_synonyms")
            curies.write_jsonld_context(
                converter, synonyms_stub.with_suffix(".context.jsonld"), include_synonyms=True
            )
            curies.write_shacl(
                converter, synonyms_stub.with_suffix(".context.ttl"), include_synonyms=True
            )


if __name__ == "__main__":
    generate_contexts()
