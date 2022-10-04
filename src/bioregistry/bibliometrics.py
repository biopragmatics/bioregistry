"""Utilities for publications."""

import typing
from collections import Counter
from typing import Iterable, List

import click
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from bioregistry import manager
from bioregistry.constants import DOCS_IMG
from bioregistry.schema.struct import Publication, deduplicate_publications


def get_oldest_publications() -> List[Publication]:
    """Get the oldest publication (by year) for each resource."""
    return deduplicate_publications(
        min(publications, key=lambda p: p.year or 0)
        for resource in manager.registry.values()
        if (publications := resource.get_publications())
    )


def get_all_publications() -> List[Publication]:
    """Get all publications for each resource."""
    return deduplicate_publications(
        publication
        for resource in manager.registry.values()
        for publication in resource.get_publications()
    )


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


@click.command()
def main():
    """Generate images."""
    publications = get_oldest_publications()
    year_counter = count_publication_years(publications)
    df = pd.DataFrame(sorted(year_counter.items()), columns=["year", "count"])

    fig, ax = plt.subplots(figsize=(8, 3.5))
    sns.barplot(data=df, ax=ax, x="year", y="count")
    ax.set_ylabel("Publications")
    ax.set_xlabel("")
    ax.set_title(f"Timeline of {len(publications):,} Publications")
    plt.xticks(rotation=45)
    fig.tight_layout()
    fig.savefig(DOCS_IMG.joinpath("bibliography_years.svg"), dpi=350)


if __name__ == "__main__":
    main()
