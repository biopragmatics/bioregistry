"""Tools for seeding collections."""

import click

import bioregistry
from bioregistry.schema import Author, Collection
from bioregistry.schema_utils import add_collection, read_collections


def get_next_id() -> str:
    """Get the next collection identifier."""
    collections = read_collections()
    max_id = int(max(c.identifier for c in collections.values()))
    new_id = max_id + 1
    return f"{new_id:07}"


def get_seed_collection(
    *,
    keywords: list[str] | None = None,
    collection_id: str | None = None,
) -> Collection:
    """Get a seed collection based on keywords."""
    if collection_id is None:
        collection_id = get_next_id()

    if not keywords:
        raise ValueError

    resources: set[str] = set()
    resources.update(
        resource.prefix
        for keyword in keywords
        for resource in bioregistry.manager.get_resources_with_keyword(keyword)
    )

    collection = Collection(
        identifier=collection_id,
        name="",
        description="",
        authors=[Author.get_charlie()],
        resources=sorted(resources),
    )
    return collection


@click.command()
@click.argument("keywords", nargs=-1)
def main(keywords: list[str]) -> None:
    """Seed a collection with prefixes having the given keywords."""
    collection = get_seed_collection(keywords=keywords)
    add_collection(collection)


if __name__ == "__main__":
    main(
        [
            "education",
            "education level",
            "education science",
            "educational resource",
            "open educational resources",
            "discipline",
        ]
    )
