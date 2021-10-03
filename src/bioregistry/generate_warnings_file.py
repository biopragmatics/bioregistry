# -*- coding: utf-8 -*-

"""Generate the warnings file.

This lists any sorts of things that should be fixed upstream, but are instead manually curated in the Bioregistry.
"""

import os
from typing import Callable

import click
import yaml

import bioregistry
from bioregistry.constants import DOCS_DATA
from bioregistry.resolve import get_external

__all__ = [
    "warnings",
]

ENTRIES = sorted(
    (prefix, resource.dict(exclude_none=True))
    for prefix, resource in bioregistry.read_registry().items()
)


def _g(predicate: Callable[[str], bool]):
    return [
        {
            "prefix": prefix,
            "name": bioregistry.get_name(prefix),
            "homepage": bioregistry.get_homepage(prefix),
        }
        for prefix in sorted(bioregistry.read_registry())
        if predicate(prefix)
    ]


@click.command()
def warnings():
    """Make warnings list."""
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

    miriam_pattern_wrong = [
        dict(
            prefix=prefix,
            name=bioregistry.get_name(prefix),
            homepage=bioregistry.get_homepage(prefix),
            correct=entry["pattern"],
            miriam=entry["miriam"]["pattern"],
        )
        for prefix, entry in ENTRIES
        if "miriam" in entry
        and "pattern" in entry
        and entry["pattern"] != entry["miriam"]["pattern"]
    ]

    miriam_embedding_rewrites = [
        dict(
            prefix=prefix,
            name=bioregistry.get_name(prefix),
            homepage=bioregistry.get_homepage(prefix),
            pattern=bioregistry.get_pattern(prefix),
            correct=entry["namespace.embedded"],
            miriam=entry["miriam"]["namespaceEmbeddedInLui"],
        )
        for prefix, entry in ENTRIES
        if "namespace.embedded" in entry
    ]

    # When are namespace rewrites required?
    miriam_prefix_rewrites = [
        dict(
            prefix=prefix,
            name=bioregistry.get_name(prefix),
            homepage=bioregistry.get_homepage(prefix),
            pattern=bioregistry.get_pattern(prefix),
            correct=entry["namespace.rewrite"],
        )
        for prefix, entry in ENTRIES
        if "namespace.rewrite" in entry
    ]

    with open(os.path.join(DOCS_DATA, "warnings.yml"), "w") as file:
        yaml.safe_dump(
            {
                "wrong_patterns": miriam_pattern_wrong,
                "embedding_rewrites": miriam_embedding_rewrites,
                "prefix_rewrites": miriam_prefix_rewrites,
            },
            file,
        )


if __name__ == "__main__":
    warnings()
