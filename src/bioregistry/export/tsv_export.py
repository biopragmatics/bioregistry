# -*- coding: utf-8 -*-

"""Export components of the bioregistry to TSV."""

import csv
import os

import click

from bioregistry import read_collections, read_metaregistry
from .. import resolve
from ..constants import DOCS_DATA
from ..utils import read_registry


@click.command()
def export_tsv():
    """Export TSV."""
    with open(os.path.join(DOCS_DATA, "collections.tsv"), "w") as file:
        writer = csv.writer(file, delimiter="\t")
        writer.writerow(COLLECTIONS_HEADER)
        writer.writerows(get_collections_rows())

    with open(os.path.join(DOCS_DATA, "metaregistry.tsv"), "w") as file:
        writer = csv.writer(file, delimiter="\t")
        writer.writerow(METAREGISTRY_HEADER)
        writer.writerows(get_metaregistry_rows())

    with open(os.path.join(DOCS_DATA, "registry.tsv"), "w") as file:
        writer = csv.writer(file, delimiter="\t")
        writer.writerow(REGISTRY_HEADER)
        writer.writerows(get_registry_rows())


COLLECTIONS_HEADER = [
    "identifier",
    "name",
    "description",
    "resources",
    "author_names",
    "author_orcids",
]
METAREGISTRY_HEADER = [
    "metaprefix",
    "name",
    "homepage",
    "description",
    "download",
    "example",
    "contact",
    "provider",
    "resolver",
    "provider_formatter",
    "resolver_formatter",
]
METAPREFIXES = [
    k
    for k in sorted(read_metaregistry())
    if k not in {"bioregistry", "biolink", "ncbi", "fairsharing", "go"}
]
REGISTRY_HEADER = [
    "identifier",
    "name",
    "homepage",
    "description",
    "pattern",
    "example",
    "email",
    "formatter",
    "download.owl",
    "download.obo",
    "synonyms",
    "deprecated",
    *METAPREFIXES,
    "part_of",
    "provides",
    # 'type',
]


def get_collections_rows():
    """Get a dataframe of all collections."""
    rows = []
    for identifier, collection in read_collections().items():
        rows.append(
            (
                identifier,
                collection.name,
                collection.description,
                "|".join(collection.resources),
                "|".join(author.name for author in collection.authors),
                "|".join(author.orcid for author in collection.authors),
            )
        )
    return rows


def get_metaregistry_rows():
    """Get a dataframe of all metaresources."""
    rows = []
    for metaprefix, data in read_metaregistry().items():
        rows.append(
            (
                metaprefix,
                data.name,
                data.homepage,
                data.description,
                data.download,
                data.example,
                data.contact,
                data.provider,
                data.resolver,
                data.provider_url,
                data.resolver_url,
            )
        )
    return rows


def get_registry_rows():
    """Get a dataframe of all resources."""
    rows = []
    for prefix, data in read_registry().items():
        mappings = resolve.get_mappings(prefix) or {}
        rows.append(
            (
                prefix,
                resolve.get_name(prefix),
                resolve.get_homepage(prefix),
                resolve.get_description(prefix),
                resolve.get_pattern(prefix),
                resolve.get_example(prefix),
                resolve.get_email(prefix),
                resolve.get_format(prefix),
                data.download_owl,
                data.download_obo,
                "|".join(data.synonyms or []),
                resolve.is_deprecated(prefix),
                *[mappings.get(metaprefix) for metaprefix in METAPREFIXES],
                # '|'.join(data.get('appears_in', [])),
                data.part_of,
                data.provides,
                # data.get('type'),
                # TODO could add more, especially mappings
            )
        )
    return rows


if __name__ == "__main__":
    export_tsv()
