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
)
from bioregistry.schema import Collection


@click.command()
def generate_context_json_ld():
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
    generate_context_json_ld()
