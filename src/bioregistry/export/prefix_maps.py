# -*- coding: utf-8 -*-

"""Export the Bioregistry as a JSON-LD context."""

import json
import logging
from pathlib import Path
from typing import Mapping, Optional, Sequence

import click

import bioregistry
from bioregistry.constants import DOCS_DATA
from bioregistry.schema import Collection

logger = logging.getLogger(__name__)


@click.command()
def generate_context_json_ld():
    """Generate various JSON-LD context files."""
    contexts_directory = Path(DOCS_DATA) / "contexts"
    contexts_directory.mkdir(parents=True, exist_ok=True)

    with contexts_directory.joinpath("obo.context.jsonld").open("w") as file:
        json.dump(
            fp=file,
            indent=4,
            sort_keys=True,
            obj={
                "@context": get_obofoundry_prefix_map(),
            },
        )

    with contexts_directory.joinpath("obo_synonyms.context.jsonld").open("w") as file:
        json.dump(
            fp=file,
            indent=4,
            sort_keys=True,
            obj={
                "@context": get_obofoundry_prefix_map(include_synonyms=True),
            },
        )

    for key, collection in bioregistry.read_collections().items():
        name = collection.context
        if name is None:
            continue
        with contexts_directory.joinpath(name).with_suffix(".context.jsonld").open("w") as file:
            json.dump(fp=file, indent=4, sort_keys=True, obj=get_collection_jsonld(key))


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
    "bioregistry",
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
    return get_general_prefix_map(
        remapping=remapping, priority=OBO_PRIORITY, include_synonyms=include_synonyms
    )


def get_general_prefix_map(
    *,
    remapping: Optional[Mapping[str, str]] = None,
    priority: Optional[Sequence[str]] = None,
    include_synonyms: bool = False,
) -> Mapping[str, str]:
    """Get the full prefix map.

    :param remapping: A mapping from bioregistry prefixes to preferred prefixes.
    :param priority: A priority list for how to generate prefix URLs.
    :param include_synonyms: Should synonyms of each prefix also be included as additional prefixes, but with
        the same URL prefix?
    :return: A mapping from prefixes to prefix URLs.
    """
    urls = bioregistry.get_format_urls(priority=priority, include_synonyms=include_synonyms)
    if remapping is None:
        return urls
    return {remapping.get(prefix, prefix): prefix_url for prefix, prefix_url in urls.items()}


if __name__ == "__main__":
    generate_context_json_ld()
