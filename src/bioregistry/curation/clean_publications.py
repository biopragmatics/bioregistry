"""Clean up the publications.

1. Remove duplications
2. Remove publications missing key metadata (e.g., title)
"""

from bioregistry import Resource
from bioregistry.curation.utils import resource_mutator
from bioregistry.schema import deduplicate_publications


def _clean_title(title: str) -> str:
    return title.rstrip(".").replace("  ", " ")


@resource_mutator()
def _main(resource: Resource) -> None:
    if not resource.publications:
        return
    new = []
    for publication in deduplicate_publications(resource.publications):
        if not publication.title:
            continue
        publication.title = _clean_title(publication.title)
        new.append(publication)
    resource.publications = sorted(new)


if __name__ == "__main__":
    _main()
