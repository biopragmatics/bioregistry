# -*- coding: utf-8 -*-

"""Export the Bioregistry as a JSON-LD context."""

import json
from pathlib import Path
from textwrap import dedent
from typing import Mapping

import click

import bioregistry
from bioregistry import get_prefix_map
from bioregistry.constants import (
    CONTEXT_BIOREGISTRY_PATH,
    CONTEXT_OBO_PATH,
    CONTEXT_OBO_SYNONYMS_PATH,
    EXPORT_CONTEXTS,
    SHACL_OBO_SYNONYMS_TURTLE_PATH,
    SHACL_OBO_TURTLE_PATH,
    SHACL_TURTLE_PATH,
)
from bioregistry.schema import Collection


@click.command()
def generate_contexts():
    """Generate various context files."""
    prefix_map = get_prefix_map()
    _write_prefix_map(CONTEXT_BIOREGISTRY_PATH, prefix_map)
    _write_shacl(SHACL_TURTLE_PATH, prefix_map)

    obo_prefix_map = get_obofoundry_prefix_map()
    _write_prefix_map(CONTEXT_OBO_PATH, obo_prefix_map)
    _write_shacl(SHACL_OBO_TURTLE_PATH, obo_prefix_map)

    obo_synonyms_prefix_map = get_obofoundry_prefix_map(include_synonyms=True)
    _write_prefix_map(CONTEXT_OBO_SYNONYMS_PATH, obo_synonyms_prefix_map)
    _write_shacl(SHACL_OBO_SYNONYMS_TURTLE_PATH, obo_synonyms_prefix_map)

    for key, collection in bioregistry.read_collections().items():
        name = collection.context
        if name is None:
            continue
        context_path_stub = EXPORT_CONTEXTS.joinpath(name)
        # Dump jsonld
        with context_path_stub.with_suffix(".context.jsonld").open("w") as file:
            json.dump(fp=file, indent=4, sort_keys=True, obj=get_collection_jsonld(key))
        # Dump shacl
        _write_shacl(context_path_stub.with_suffix(".context.ttl"), prefix_map)


def _write_shacl(path: Path, prefix_map: Mapping[str, str]) -> None:
    text = dedent(
        """\
        @prefix sh: <http://www.w3.org/ns/shacl#> .

        [
          sh:declare
        {entries}
        ] .
        """
    )
    entries = ",\n".join(
        f'    [ sh:prefix "{prefix}" ; sh:namespace "{uri_prefix}" ]'
        for prefix, uri_prefix in prefix_map.items()
    )
    path.write_text(text.format(entries=entries))


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
