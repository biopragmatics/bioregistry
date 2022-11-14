"""Clean up the publications.

1. Remove duplications
2. Remove publications missing key metadat (e.g., title)
"""

from tqdm import tqdm

import bioregistry
from bioregistry.schema.struct import deduplicate_publications


def _main():
    for resource in tqdm(bioregistry.resources()):
        if resource.publications:
            resource.publications = [
                p for p in deduplicate_publications(resource.publications) if p.title
            ]
    bioregistry.manager.write_registry()


if __name__ == "__main__":
    _main()
