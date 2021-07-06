# -*- coding: utf-8 -*-

"""Make the curation list."""

import os
from typing import Callable

import click
import yaml

import bioregistry
from bioregistry.constants import DOCS_DATA
from bioregistry.resolve import get_external


def _g(predicate: Callable[[str], bool]):
    return [
        {
            "prefix": prefix,
            "name": bioregistry.get_name(prefix),
        }
        for prefix in sorted(bioregistry.read_registry())
        if predicate(prefix)
    ]


@click.command()
def curation():
    """Make curation list."""
    missing_wikidata_database = _g(
        lambda prefix: get_external(prefix, "wikidata").get("database") is None
    )
    missing_pattern = _g(lambda prefix: bioregistry.get_pattern(prefix) is None)
    missing_format_url = _g(lambda prefix: bioregistry.get_format(prefix) is None)
    missing_example = _g(lambda prefix: bioregistry.get_example(prefix) is None)

    with open(os.path.join(DOCS_DATA, "curation.yml"), "w") as file:
        yaml.safe_dump(
            {
                "wikidata": missing_wikidata_database,
                "pattern": missing_pattern,
                "formatter": missing_format_url,
                "example": missing_example,
            },
            file,
        )


if __name__ == "__main__":
    curation()
