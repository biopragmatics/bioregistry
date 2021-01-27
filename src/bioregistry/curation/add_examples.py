# -*- coding: utf-8 -*-

"""Script for adding examples automatically."""

import random
import urllib.error
from typing import Optional

import pyobo
import pyobo.getters

from bioregistry.utils import updater


@updater
def main(registry):
    """Add examples to the bioregistry from OBO/OLS."""
    for prefix, entry in registry.items():
        # if 'pattern' not in entry:  # TODO remove this later
        #     continue
        if 'example' in entry:
            continue
        example = _get_example(prefix)
        if example is not None:
            entry['example'] = example
    return registry


def _get_example(prefix: str) -> Optional[str]:
    if prefix in {'gaz', 'bila', 'pubchem.compound'}:
        return
    if prefix in pyobo.getters.SKIP:
        return
    try:
        x = pyobo.get_id_name_mapping(prefix)
    except (pyobo.getters.NoBuild, ValueError, urllib.error.URLError):
        return
    if not x:
        return
    x = list(x)
    try:
        rv = x[random.randint(0, len(x))]  # noqa:S311
    except IndexError:
        print('failed', prefix, x)
    else:
        print('adding', prefix, rv)
        return rv


if __name__ == '__main__':
    main()
