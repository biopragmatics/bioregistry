# -*- coding: utf-8 -*-

"""Script for adding examples automatically."""

import random
from typing import Optional

import click

import bioregistry
import bioregistry.utils
import pyobo
import pyobo.getters


@click.command()
def main():
    """Add examples to the bioregistry from OBO/OLS."""
    registry = bioregistry.read_bioregistry()
    for prefix, entry in registry.items():
        if 'pattern' not in entry:  # TODO remove this later
            continue
        if 'example' in entry:
            continue
        example = _get_example(prefix)
        if example is not None:
            entry['example'] = example
    bioregistry.utils.write_bioregistry(registry)


def _get_example(prefix: str) -> Optional[str]:
    if prefix in {'gaz'}:
        return
    try:
        x = pyobo.get_id_name_mapping(prefix)
    except (pyobo.getters.NoBuild, ValueError):
        return
    if not x:
        return
    x = list(x)
    try:
        rv = x[random.randint(0, len(x))]
    except IndexError:
        print('failed', prefix, x)
    else:
        print('adding', prefix, rv)
        return rv


if __name__ == '__main__':
    main()
