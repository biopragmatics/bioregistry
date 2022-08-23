import pystow
from bioregistry import Manager, resources, write_registry
from bioregistry.app.impl import get_app

MODULE = pystow.module("bioregistry", "demo")
REGISTRY_PATH = MODULE.join(name="custom_registry.json")

PREFIXES = {"genepio", "go", "uberon", "doid", "mondo", "ido", "cido"}
if not REGISTRY_PATH.is_file():
    # Generate a slim
    slim_registry = {resource.prefix: resource for resource in resources() if resource.prefix in PREFIXES}
    write_registry(slim_registry, path=REGISTRY_PATH)
    print("wrote registry to", REGISTRY_PATH)

manager = Manager(registry=REGISTRY_PATH, collections={}, contexts={})
config = {
    "METAREGISTRY_TITLE": "Custom Metaregistry",
    "METAREGISTRY_FOOTER": "This is a custom instance of the Bioregistry",
    "METAREGISTRY_HEADER": "",
    "METAREGISTRY_VERSION": "0.0.0",
    "METAREGISTRY_HOST": "localhost:5000",
}
app = get_app(manager=manager, config=config)

if __name__ == '__main__':
    app.run()
