"""Clean up the publications.

1. Remove duplications
2. Remove publications missing key metadata (e.g., title)
"""

import click

import bioregistry
from bioregistry.schema import deduplicate_publications


@click.command()
def _main() -> None:
    for resource in bioregistry.manager.registry.values():
        if resource.publications:
            new = []
            for p in deduplicate_publications(resource.publications):
                if not p.title:
                    continue
                p.title = p.title.rstrip(".").replace("  ", " ")
                new.append(p)
            resource.publications = sorted(new)
    bioregistry.manager.write_registry()


if __name__ == "__main__":
    _main()
