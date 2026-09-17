"""Export TSV."""

from __future__ import annotations

from collections.abc import Sequence

import click
from pystow.utils import safe_open_writer

from ..constants import (
    COLLECTIONS_TSV_PATH,
    METAREGISTRY_TSV_PATH,
    REGISTRY_TSV_PATH,
    URI_FORMAT_KEY,
)
from ..resource_manager import Manager
from ..schema_utils import read_collections
from ..uri_format import get_uri_format


@click.command()
def export_tsv() -> None:
    """Export TSV."""
    manager = Manager()

    with safe_open_writer(COLLECTIONS_TSV_PATH) as writer:
        writer.writerow(COLLECTIONS_HEADER)
        writer.writerows(get_collections_rows())

    with safe_open_writer(METAREGISTRY_TSV_PATH) as writer:
        writer.writerow(METAREGISTRY_HEADER)
        writer.writerows(get_metaregistry_rows(manager))

    with safe_open_writer(REGISTRY_TSV_PATH) as writer:
        writer.writerow(_get_registry_header(manager))
        writer.writerows(get_registry_rows(manager))


COLLECTIONS_HEADER = [
    "identifier",
    "name",
    "description",
    "resources",
    "contributor_names",
    "contributor_orcids",
    "maintainer_names",
    "maintainer_orcids",
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


def _get_metaprefixes(manager: Manager) -> list[str]:
    return [
        k
        for k in sorted(manager.metaregistry)
        if k not in {"bioregistry", "biolink", "ncbi", "fairsharing", "go"}
    ]


def _get_registry_header(manager: Manager) -> list[str]:
    return [
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
        *_get_metaprefixes(manager),
        "part_of",
        "provides",
        "has_canonical",
        # 'type',
    ]


def get_collections_rows() -> list[tuple[str, str, str, str, str, str, str, str]]:
    """Get a dataframe of all collections."""
    rows = []
    for identifier, collection in read_collections().items():
        rows.append(
            (
                identifier,
                collection.name,
                collection.description,
                "|".join(collection.get_prefixes()),
                "|".join(
                    contributor.name
                    for contributor in collection.contributors or []
                    if contributor.orcid
                ),
                "|".join(
                    contributor.orcid
                    for contributor in collection.contributors or []
                    if contributor.orcid
                ),
                "|".join(
                    maintainer.name
                    for maintainer in collection.maintainers or []
                    if maintainer.orcid
                ),
                "|".join(
                    maintainer.orcid
                    for maintainer in collection.maintainers or []
                    if maintainer.orcid
                ),
            )
        )
    return rows


def get_metaregistry_rows(manager: Manager | None = None) -> list[tuple[str, ...]]:
    """Get a dataframe of all metaresources."""
    if manager is None:
        manager = Manager()
    rows: list[tuple[str, ...]] = []
    for metaprefix, data in manager.metaregistry.items():
        rows.append(
            (
                metaprefix,
                data.name,
                data.homepage,
                data.description,
                data.download or "",
                data.example,
                data.contact.name,
                data.contact.email or "",
                data.contact.github or "",
                data.uri_format or "",
                data.resolver_uri_format or "",
                data.resolver_type or "",
            )
        )
    return rows


def get_registry_rows(manager: Manager | None = None) -> list[Sequence[str | None]]:
    """Get a dataframe of all resources."""
    if manager is None:
        manager = Manager()
    metaprefixes = _get_metaprefixes(manager)
    rows: list[Sequence[str | None]] = []
    for prefix, data in manager.registry.items():
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
                str(data.is_deprecated()),
                *[mappings.get(metaprefix) for metaprefix in metaprefixes],
                data.part_of,
                data.provides,
                data.has_canonical,
                # TODO could add more, especially mappings
            )
        )
    return rows


if __name__ == "__main__":
    export_tsv()
