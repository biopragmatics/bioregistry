"""A custom deploymenet."""

import pystow

from bioregistry import Manager, get_collection, resources, write_registry
from bioregistry.app.impl import get_app

MODULE = pystow.module("bioregistry", "demo")
REGISTRY_PATH = MODULE.join(name="custom_registry.json")

PREFIXES = {"genepio", "go", "uberon", "doid", "mondo", "ido", "cido"}
COLLECTIONS = {
    "0000002",  # semantic web
    "0000006",  # publishing
}
PREFIXES.update(
    prefix
    for collection_id in COLLECTIONS
    for prefix in get_collection(collection_id).resources  # type:ignore
)
PREFIXES.update(resource.prefix for resource in resources() if "bioregistry" in resource.prefix)

if not REGISTRY_PATH.is_file() or True:
    # Generate a slim
    slim_registry = {
        resource.prefix: resource for resource in resources() if resource.prefix in PREFIXES
    }
    write_registry(slim_registry, path=REGISTRY_PATH)

manager = Manager(registry=REGISTRY_PATH, collections={}, contexts={})
config = {
    "METAREGISTRY_TITLE": "Custom Metaregistry",
    "METAREGISTRY_FOOTER": "This is a custom instance of the Bioregistry",
    "METAREGISTRY_HEADER": "<p>This is a custom instance of the Bioregistry, for demo purposes</p>",
    "METAREGISTRY_RESOURCES_SUBHEADER": "",
    "METAREGISTRY_VERSION": "",
    "METAREGISTRY_HOST": "http://localhost:5000",
    "METAREGISTRY_EXAMPLE_PREFIX": "ido",
}
app = get_app(manager=manager, config=config)

if __name__ == "__main__":
    app.run()
