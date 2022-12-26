"""Add bartoc mappings via wikidata."""

import bioregistry
from bioregistry import manager
from bioregistry.external.bartoc import get_bartoc


def _main():
    wikidata_database_to_bioregistry = {
        resource.wikidata["database"]: resource.prefix
        for resource in bioregistry.resources()
        if resource.wikidata and "database" in resource.wikidata
    }
    wikidata_database_to_bartoc = {
        value["wikidata_database"]: key
        for key, value in get_bartoc(force_download=False).items()
        if "wikidata_database" in value
    }
    for wikidata_id, prefix in wikidata_database_to_bioregistry.items():
        bartoc_id = wikidata_database_to_bartoc.get(wikidata_id)
        if bartoc_id:
            manager.registry[prefix].mappings["bartoc"] = bartoc_id
    manager.write_registry()


if __name__ == "__main__":
    _main()
