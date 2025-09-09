"""Clean up the publications.

1. Remove duplications
2. Remove publications missing key metadat (e.g., title)
"""

from tqdm import tqdm

import bioregistry
from bioregistry.schema.struct import deduplicate_publications


def _main() -> None:
    for resource in tqdm(bioregistry.manager.registry.values()):
        if resource.publications:
            new = []
            for p in deduplicate_publications(resource.publications):
                if not p.title:
                    continue
                p.title = p.title.rstrip(".").replace("  ", " ")
                new.append(p)
            resource.publications = new
    bioregistry.manager.write_registry()


if __name__ == "__main__":
    _main()
