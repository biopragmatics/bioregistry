"""Utilities for working with the data produced by the semi-automated curation workflow."""

import enum

import click

__all__ = [
    "CurationRelevance",
    "COLUMNS",
]

COLUMNS = [
    "pmid",
    "relevant",
    "relevancy_type",
    "orcid",
    "date_curated",
    "notes",
    "pr_added",  # links back to the PR where curations were done
]


class CurationRelevance(str, enum.Enum):
    """An enumeration for curation relevance."""

    #: A resource for new primary identifiers
    new_prefix = enum.auto()
    new_provider = enum.auto()
    new_publication = enum.auto()
    not_identifiers_resource = enum.auto()
    no_website = enum.auto()
    existing = enum.auto()
    unclear = enum.auto()
    irrelevant_other = enum.auto()


@click.command()
def main():
    """Import data from the literature curation into the Bioregistry."""
    raise NotImplementedError


if __name__ == "__main__":
    main()
