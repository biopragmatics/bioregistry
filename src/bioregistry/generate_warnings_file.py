# -*- coding: utf-8 -*-

"""Generate the warnings file.

This lists any sorts of things that should be fixed upstream, but are instead manually curated in the Bioregistry.
"""

import os

import click
import yaml

import bioregistry
from bioregistry.constants import DOCS_DATA

__all__ = [
    "warnings",
]

items = sorted(bioregistry.read_registry().items())


@click.command()
def warnings():
    """Make warnings list."""
    miriam_pattern_wrong = [
        dict(
            prefix=prefix,
            name=bioregistry.get_name(prefix),
            correct=entry["pattern"],
            miriam=entry["miriam"]["pattern"],
        )
        for prefix, entry in items
        if "miriam" in entry
        and "pattern" in entry
        and entry["pattern"] != entry["miriam"]["pattern"]
    ]

    miriam_embedding_rewrites = [
        dict(
            prefix=prefix,
            name=bioregistry.get_name(prefix),
            pattern=bioregistry.get_pattern(prefix),
            correct=entry["namespace.embedded"],
            miriam=entry["miriam"]["namespaceEmbeddedInLui"],
        )
        for prefix, entry in items
        if "namespace.embedded" in entry
    ]

    # When are namespace rewrites required?
    miriam_prefix_rewrites = [
        dict(
            prefix=prefix,
            name=bioregistry.get_name(prefix),
            pattern=bioregistry.get_pattern(prefix),
            correct=entry["namespace.rewrite"],
        )
        for prefix, entry in items
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
