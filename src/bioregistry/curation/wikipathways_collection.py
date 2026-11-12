"""Update the WikiPathways collection."""

from typing import cast

import click
from tabulate import tabulate

from bioregistry import Manager
from bioregistry.schema.struct import CollectionAnnotation
from bioregistry.validate.utils import get_sparql_shacl_prefix_map, get_virtuoso_prefix_map

CONFIGURATIONS = [
    ("0000048", "WikiPathways", "https://sparql.wikipathways.org/sparql", True),
    ("0000049", "Rhea", "https://sparql.rhea-db.org/sparql", False),
    ("0000050", "AOP Wiki", "https://aopwiki.rdf.bigcat-bioinformatics.org//sparql", True),
]


def _update_collection(
    manager: Manager, name: str, collection_id: str, endpoint: str, *, virtuoso: bool = False
) -> None:
    collection = manager.collections[collection_id]
    resources: set[str] = set(collection.get_prefixes())
    missing: list[tuple[str, str]] = []
    prefix_maps = [
        get_sparql_shacl_prefix_map(endpoint),
    ]
    if virtuoso:
        try:
            virtuoso_prefix_map = get_virtuoso_prefix_map(endpoint)
        except ValueError:
            click.echo(f"[{name}] failed to get NSDECL prefix map - maybe it's not virtuoso?")
        else:
            prefix_maps.append(virtuoso_prefix_map)
    for prefix_map in prefix_maps:
        for prefix, uri_prefix in prefix_map.items():
            resource = manager.get_resource(prefix)
            if resource is not None:
                resources.add(resource.prefix)
            else:
                missing.append((prefix, uri_prefix))
    collection.resources = cast(list[str | CollectionAnnotation], sorted(resources))
    if missing:
        click.echo(f"Missing resources in {name}:\n")
        click.echo(tabulate(missing, headers=["prefix", "uri_prefix"], tablefmt="github") + "\n")


@click.command()
def main() -> None:
    """Update the WikiPathways collection."""
    manager = Manager()
    for collection_id, name, endpoint, virtuoso in CONFIGURATIONS:
        _update_collection(manager, name, collection_id, endpoint, virtuoso=virtuoso)
    manager.write_collections()


if __name__ == "__main__":
    main()
