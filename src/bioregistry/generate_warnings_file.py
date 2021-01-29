# -*- coding: utf-8 -*-

"""Generate the warnings file.

This lists any sorts of things that should be fixed upstream, but are instead manually curated in the Bioregistry.
"""

import os

import click
import yaml

from bioregistry import get_name, get_pattern, read_bioregistry
from bioregistry.constants import DOCS_DATA

__all__ = [
    'warnings',
]

items = sorted(read_bioregistry().items())


@click.command()
def warnings():
    """Make warnings list."""
    # When are namespace rewrites required?
    miriam_rewrites = [
        dict(
            prefix=prefix,
            name=get_name(prefix),
            pattern=get_pattern(prefix),
            correct=entry['namespace.rewrite'],
        )
        for prefix, entry in items
        if 'namespace.rewrite' in entry
    ]

    embedding_rewrites = [
        dict(
            prefix=prefix,
            name=get_name(prefix),
            pattern=get_pattern(prefix),
            correct=entry['namespace.embedded'],
            miriam=entry['miriam']['namespaceEmbeddedInLui'],
        )
        for prefix, entry in items
        if 'namespace.embedded' in entry
    ]

    miriam_pattern_wrong = [
        dict(
            prefix=prefix,
            name=get_name(prefix),
            correct_pattern=entry['pattern'],
            miriam_pattern=entry['miriam']['pattern'],
        )
        for prefix, entry in items
        if 'miriam' in entry and 'pattern' in entry and entry['pattern'] != entry['miriam']['pattern']
    ]

    with open(os.path.join(DOCS_DATA, 'warnings.yml'), 'w') as file:
        yaml.safe_dump(
            {
                'prefix_rewrites': miriam_rewrites,
                'embedding_rewrites': embedding_rewrites,
                'wrong_patterns': miriam_pattern_wrong,
            },
            file,
        )


if __name__ == '__main__':
    warnings()
