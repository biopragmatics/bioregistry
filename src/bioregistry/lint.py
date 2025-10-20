"""Linting functions."""

import click

__all__ = [
    "lint",
]


@click.command()
def lint() -> None:
    """Run the lint commands."""
    from .constants import CURATED_PAPERS_PATH
    from .schema_utils import (
        read_collections,
        read_contexts,
        read_mappings,
        read_metaregistry,
        read_registry,
        write_collections,
        write_contexts,
        write_mappings,
        write_metaregistry,
        write_registry,
    )

    # clear LRU caches so if this is run after some functions that update
    # these resources, such as the align() pipeline, they don't get overwritten.
    for read_resource_func in (
        read_registry,
        read_mappings,
        read_metaregistry,
        read_collections,
        read_contexts,
    ):
        read_resource_func.cache_clear()
    # Import here to avoid dependency in the context of
    # web app / Docker
    import pandas as pd

    registry = read_registry()
    for resource in registry.values():
        if resource.synonyms:
            resource.synonyms = sorted(set(resource.synonyms))
        if resource.keywords:
            resource.keywords = sorted({k.lower() for k in resource.keywords})

        if resource.publications:
            resource.publications = sorted(resource.publications)

        for provider in resource.providers or []:
            if provider.publications:
                provider.publications = sorted(provider.publications)

    write_registry(registry)
    collections = read_collections()
    for collection in collections.values():
        collection.resources = sorted(set(collection.resources))
    write_collections(collections)
    write_metaregistry(read_metaregistry())
    write_contexts(read_contexts())
    write_mappings(read_mappings())

    df = pd.read_csv(CURATED_PAPERS_PATH, sep="\t")
    df["pr_added"] = df["pr_added"].map(lambda x: str(int(x)) if pd.notna(x) else None)
    df = df.sort_values(["pubmed"])
    df.to_csv(CURATED_PAPERS_PATH, index=False, sep="\t")


if __name__ == "__main__":
    lint()
