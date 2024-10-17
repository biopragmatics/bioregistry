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
    "pr_added",  # links back to the PR where curations were done
    "orcid",
    "date_curated",
    "notes",
]


class CurationRelevance(str, enum.Enum):
    """An enumeration for curation relevance."""

    #: A resource for new primary identifiers
    new_prefix = enum.auto()
    #: A resolver for existing identifiers
    new_provider = enum.auto()
    #: A new publication for an existing prefix
    new_publication = enum.auto()
    #: A database, but not for identifier information
    not_identifiers_resource = enum.auto()
    #: Paper suggestive of a new database, but no link to website provided
    no_website = enum.auto()
    #: An existing entry in the bioregistry
    existing = enum.auto()
    #: Not clear how to curate in the bioregistry, follow up discussion required
    unclear = enum.auto()
    #: Completely unrelated information
    irrelevant_other = enum.auto()


@click.command()
def main():
    """Import data from the literature curation into the Bioregistry."""
    raise NotImplementedError


if __name__ == "__main__":
    main()
