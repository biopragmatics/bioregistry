# -*- coding: utf-8 -*-

"""Utilities for publications."""

import typing
from collections import Counter
from typing import TYPE_CHECKING, Iterable, List

from .resource_manager import manager
from .schema.struct import Publication, deduplicate_publications

if TYPE_CHECKING:
    import pandas


def get_oldest_publications() -> List[Publication]:
    """Get the oldest publication (by year) for each resource."""
    publications = []
    for resource in manager.registry.values():
        resource_publications = resource.get_publications()
        if resource_publications:
            publications.append(min(resource_publications, key=lambda p: p.year or 0))
    return deduplicate_publications(publications)


def get_all_publications() -> List[Publication]:
    """Get all publications for each resource."""
    return deduplicate_publications(
        publication
        for resource in manager.registry.values()
        for publication in resource.get_publications()
    )


def get_publications_df() -> "pandas.DataFrame":
    """Get a dataframe with all publications."""
    import pandas

    rows = []
    for publication in get_all_publications():
        rows.append(
            (
                publication.pubmed,
                publication.doi,
                publication.pmc,
                str(publication.year) if publication.year else None,
                publication.title,
            )
        )
    df = pandas.DataFrame(
        rows,
        columns=["pubmed", "doi", "pmc", "year", "title"],
        dtype=str,
    ).sort_values(["pubmed", "doi", "pmc"])
    return df


def count_publication_years(
    publications: Iterable[Publication], minimum_year: int = 1995
) -> typing.Counter[int]:
    """Count the number of publications for resources in the Bioregistry for each year."""
    year_counter = Counter(
        publication.year
        for publication in publications
        if publication.year and publication.year >= minimum_year
    )
    for i in range(min(year_counter) - 1, max(year_counter) + 1):
        if i not in year_counter:
            year_counter[i] = 0
    return year_counter
