"""Update the WikiPathways collection."""

from typing import cast

import click
from tabulate import tabulate

from bioregistry import Collection, Manager
from bioregistry.schema.struct import CollectionAnnotation
from bioregistry.validate.utils import get_sparql_shacl_prefix_map, get_virtuoso_prefix_map

WIKIPATHWAYS_COLLECTION_ID = "0000048"

ENDPOINT = "https://sparql.wikipathways.org/sparql"


def _update_collection(manager: Manager, collection: Collection) -> None:
    resources: set[str] = set(collection.get_prefixes())
    missing: list[tuple[str, str]] = []
    for prefix_map in [
        get_sparql_shacl_prefix_map(ENDPOINT),
        get_virtuoso_prefix_map(ENDPOINT),
    ]:
        for prefix, uri_prefix in prefix_map.items():
            resource = manager.get_resource(prefix)
            if resource is not None:
                resources.add(resource.prefix)
            else:
                missing.append((prefix, uri_prefix))
    collection.resources = cast(list[str | CollectionAnnotation], sorted(resources))
    if missing:
        click.echo("Missing resources:\n")
        click.echo(tabulate(missing, headers=["prefix", "uri_prefix"], tablefmt="github"))


@click.command()
def main() -> None:
    """Update the WikiPathways collection."""
    manager = Manager()
    collection = manager.collections[WIKIPATHWAYS_COLLECTION_ID]
    _update_collection(manager, collection)
    manager.write_collections()


if __name__ == "__main__":
    main()
