"""Linting functions."""

import click

__all__ = [
    "lint",
]


@click.command()
def lint() -> None:
    """Run the lint commands."""
    import sssom_pydantic

    from .constants import CURATED_MAPPINGS_PATH, CURATED_PAPERS_PATH
    from .schema_utils import (
        _lint_collection_resources,
        read_collections,
        read_contexts,
        read_mappings,
        read_metaregistry,
        read_mismatches,
        read_registry,
        write_collections,
        write_contexts,
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
    mismatches = read_mismatches()
    for resource in registry.values():
        if resource.synonyms:
            resource.synonyms = sorted(set(resource.synonyms))
        if resource.keywords:
            resource.keywords = sorted({k.lower().strip() for k in resource.keywords})

        if resource.publications:
            resource.publications = sorted(resource.publications)
            for publication in resource.publications:
                if publication.doi:
                    publication.doi = publication.doi.lower()

        for provider in resource.providers or []:
            if provider.publications:
                provider.publications = sorted(provider.publications)

        if resource.homepage:
            resource.homepage = resource.homepage.rstrip("/")
        if resource.repository:
            resource.repository = resource.repository.rstrip("/")

        if resource.mappings:
            for external_registry, external_prefixes in mismatches.get(resource.prefix, {}).items():
                if (
                    external_registry in resource.mappings
                    and resource.mappings[external_registry] in external_prefixes
                ):
                    del resource.mappings[external_registry]
                    setattr(resource, external_registry, None)

    write_registry(registry)
    collections = read_collections()
    for collection in collections.values():
        collection.resources = _lint_collection_resources(collection.resources)
    write_collections(collections)
    write_metaregistry(read_metaregistry())
    write_contexts(read_contexts())

    sssom_pydantic.format(CURATED_MAPPINGS_PATH)

    df = pd.read_csv(CURATED_PAPERS_PATH, sep="\t")
    df["pr_added"] = df["pr_added"].map(lambda x: str(int(x)) if pd.notna(x) else None)
    df = df.sort_values(["pubmed"])
    df.to_csv(CURATED_PAPERS_PATH, index=False, sep="\t")


if __name__ == "__main__":
    lint()
