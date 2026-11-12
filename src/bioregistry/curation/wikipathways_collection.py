"""Update the WikiPathways collection."""

import click

from bioregistry import Collection, Manager
from bioregistry.validate.utils import get_shacl_defined

WIKIPATHWAYS_COLLECTION_ID = "0000048"

ENDPOINT = "https://sparql.wikipathways.org/sparql"


def _update_collection(manager: Manager, collection: Collection) -> None:
    resources: set[str] = set(collection.get_prefixes())
    prefix_map = get_shacl_defined(ENDPOINT)
    for prefix, uri_prefix in prefix_map.items():
        resource = manager.get_resource(prefix)
        if resource is not None:
            resources.add(resource.prefix)
        else:
            click.echo(f"No resource for {prefix} - {uri_prefix}")
    collection.resources = sorted(resources)


@click.command()
def main() -> None:
    """Update the WikiPathways collection."""
    manager = Manager()
    collection = manager.collections[WIKIPATHWAYS_COLLECTION_ID]
    _update_collection(manager, collection)
    manager.write_collections()


if __name__ == "__main__":
    main()
