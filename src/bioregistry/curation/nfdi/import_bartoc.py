"""Import BARTOC collections."""

import click
from tabulate import tabulate
from tqdm import tqdm

import bioregistry
from bioregistry.external import get_bartoc
from bioregistry.external.bartoc import get_bartoc_registries
from bioregistry.schema_utils import get_collection_mappings


@click.command()
def import_bartoc() -> None:
    """Import BARTOC collections."""
    rows = []
    bartoc_registries = get_bartoc_registries()
    bartoc_to_internal = bioregistry.get_registry_invmap("bartoc")
    bartoc_data = get_bartoc()

    for collection_id, registry_bartoc_id in get_collection_mappings("bartoc").items():
        for resource_bartoc_id in bartoc_registries[registry_bartoc_id]:
            prefix = bartoc_to_internal.get(resource_bartoc_id)
            if prefix:
                bioregistry.add_to_collection(collection_id, prefix)
            else:
                rows.append(
                    (
                        resource_bartoc_id,
                        f"https://bartoc.org/node/{resource_bartoc_id}",
                        bartoc_data[resource_bartoc_id].get("short_names"),
                        bartoc_data[resource_bartoc_id].get("name"),
                        bartoc_data[resource_bartoc_id].get("homepage"),
                        bartoc_data[resource_bartoc_id].get("uri_format"),
                    )
                )
    bioregistry.manager.write_collections()
    tqdm.write(
        tabulate(
            rows,
            headers=["bartoc", "bartoc link", "prefix", "name", "homepage", "uri_format"],
            showindex=False,
        )
    )


if __name__ == "__main__":
    import_bartoc()
