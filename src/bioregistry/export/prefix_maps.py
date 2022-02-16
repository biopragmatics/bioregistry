# -*- coding: utf-8 -*-

"""Export the Bioregistry as a JSON-LD context."""

import json
from pathlib import Path
from typing import Mapping

import click

import bioregistry
from bioregistry import get_prefix_map
from bioregistry.constants import (
    CONTEXT_BIOREGISTRY_PATH,
    CONTEXT_OBO_PATH,
    CONTEXT_OBO_SYNONYMS_PATH,
    EXPORT_CONTEXTS,
    SHACL_TURTLE_PATH,
)
from bioregistry.schema import Collection


@click.command()
def generate_contexts():
    """Generate various JSON-LD context files."""
    _write_prefix_map(CONTEXT_BIOREGISTRY_PATH, get_prefix_map())
    _write_prefix_map(CONTEXT_OBO_PATH, get_obofoundry_prefix_map())
    _write_prefix_map(CONTEXT_OBO_SYNONYMS_PATH, get_obofoundry_prefix_map(include_synonyms=True))

    for key, collection in bioregistry.read_collections().items():
        name = collection.context
        if name is None:
            continue
        with EXPORT_CONTEXTS.joinpath(name).with_suffix(".context.jsonld").open("w") as file:
            json.dump(fp=file, indent=4, sort_keys=True, obj=get_collection_jsonld(key))


@click.command()
def generate_shacl_prefixes():
    """Generate a SHACL prefixes file."""
    # TODO: store in context folder
    # TODO put this inside :func:`generate_contexts`
    _write_shacl(SHACL_TURTLE_PATH, get_prefix_map())


def _write_shacl(path: Path, prefix_map: Mapping[str, str]) -> None:
    text = """@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
[
    sh:declare
{entries}
] ."""
    # Todo: Should we really uppercase prefixes?
    path.parent.mkdir(parents=True, exist_ok=True)
    entries = ",\n".join(
        f'    [ sh:prefix "{prefix.upper()}" ; sh:namespace "{url}" ]'
        for prefix, url in prefix_map.items()
    )
    with path.open("w") as file:
        file.write(text.format(entries=entries))


def _write_prefix_map(path: Path, prefix_map: Mapping[str, str]) -> None:
    with path.open("w") as file:
        json.dump(
            fp=file,
            indent=4,
            sort_keys=True,
            obj={
                "@context": prefix_map,
            },
        )


def get_collection_jsonld(identifier: str) -> Mapping[str, Mapping[str, str]]:
    """Get the JSON-LD context based on a given collection."""
    collection = bioregistry.get_collection(identifier)
    if collection is None:
        raise KeyError
    return collection.as_context_jsonld()


def collection_to_context_jsonlds(collection: Collection) -> str:
    """Get the JSON-LD context as a string from a given collection."""
    return json.dumps(collection.as_context_jsonld())


OBO_PRIORITY = (
    "obofoundry",
    "default",
    "prefixcommons",
    "miriam",
    "ols",
)
OBO_REMAPPING = {
    "umls": "UMLS",
    "snomedct": "SCTID",
    "ensembl": "ENSEMBL",
}


def get_obofoundry_prefix_map(include_synonyms: bool = False) -> Mapping[str, str]:
    """Get the OBO Foundry prefix map.

    :param include_synonyms: Should synonyms of each prefix also be included as additional prefixes, but with
        the same URL prefix?
    :return: A mapping from prefixes to prefix URLs.
    """
    remapping = bioregistry.get_registry_map("obofoundry")
    remapping.update(OBO_REMAPPING)
    return get_prefix_map(
        remapping=remapping,
        priority=OBO_PRIORITY,
        include_synonyms=include_synonyms,
        use_preferred=True,
    )


if __name__ == "__main__":
    generate_contexts()
    generate_shacl_prefixes()  # TODO delete
