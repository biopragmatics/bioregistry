# -*- coding: utf-8 -*-

"""Export components of the bioregistry to TSV."""

import csv

import click

from ..constants import (
    COLLECTIONS_TSV_PATH,
    METAREGISTRY_TSV_PATH,
    REGISTRY_TSV_PATH,
    URI_FORMAT_KEY,
)
from ..schema_utils import read_collections, read_metaregistry, read_registry
from ..uri_format import get_uri_format


@click.command()
def export_tsv():
    """Export TSV."""
    with COLLECTIONS_TSV_PATH.open("w") as file:
        writer = csv.writer(file, delimiter="\t")
        writer.writerow(COLLECTIONS_HEADER)
        writer.writerows(get_collections_rows())

    with METAREGISTRY_TSV_PATH.open("w") as file:
        writer = csv.writer(file, delimiter="\t")
        writer.writerow(METAREGISTRY_HEADER)
        writer.writerows(get_metaregistry_rows())

    with REGISTRY_TSV_PATH.open("w") as file:
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
    "contact.name",
    "contact.email",
    "contact.github",
    "provider_uri_format",
    "resolver_uri_format",
    "resolver_type",
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
    URI_FORMAT_KEY,
    "download.owl",
    "download.obo",
    "synonyms",
    "deprecated",
    *METAPREFIXES,
    "part_of",
    "provides",
    "has_canonical",
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
                data.contact.name,
                data.contact.email,
                data.contact.github,
                data.provider_uri_format,
                data.resolver_uri_format,
                data.resolver_type,
            )
        )
    return rows


def get_registry_rows():
    """Get a dataframe of all resources."""
    rows = []
    for prefix, data in read_registry().items():
        mappings = data.get_mappings()
        rows.append(
            (
                prefix,
                data.get_name(),
                data.get_homepage(),
                data.get_description(),
                data.get_pattern(),
                data.get_example(),
                data.get_contact_email(),
                get_uri_format(prefix),
                data.download_owl,
                data.download_obo,
                "|".join(sorted(data.get_synonyms())),
                data.is_deprecated(),
                *[mappings.get(metaprefix) for metaprefix in METAPREFIXES],
                # '|'.join(data.get('appears_in', [])),
                data.part_of,
                data.provides,
                data.has_canonical,
                # data.get('type'),
                # TODO could add more, especially mappings
            )
        )
    return rows


if __name__ == "__main__":
    export_tsv()
