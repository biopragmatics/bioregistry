# -*- coding: utf-8 -*-

"""Download registry information from the OBO Foundry."""

import json
import os
from operator import itemgetter
from typing import Optional

import click
import yaml

from .utils import list_to_map
from ..constants import BIOREGISTRY_MODULE

__all__ = [
    'OBOFOUNDRY_FULL_PATH',
    'OBOFOUNDRY_URL',
    'get_obofoundry',
]

OBOFOUNDRY_FULL_PATH = BIOREGISTRY_MODULE.join(name='obofoundry.json')
OBOFOUNDRY_URL = 'https://raw.githubusercontent.com/OBOFoundry/OBOFoundry.github.io/master/registry/ontologies.yml'


def get_obofoundry(
    cache_path: Optional[str] = OBOFOUNDRY_FULL_PATH,
    mappify: bool = False,
    force_download: bool = False,
    skip_deprecated: bool = False,
):
    """Get the OBO Foundry registry."""
    if not force_download and cache_path is not None and os.path.exists(cache_path):
        with open(cache_path) as file:
            entries = json.load(file)
    else:
        with BIOREGISTRY_MODULE.ensure(url=OBOFOUNDRY_URL, name='obofoundry.yml').open() as file:
            entries = yaml.full_load(file)['ontologies']

        for entry in entries:
            for key in ('browsers', 'usages', 'depicted_by', 'products'):
                if key in entry:
                    del entry[key]

        # maintain sorted OBO Foundry
        entries = sorted(entries, key=itemgetter('id'))

        if cache_path is not None:
            with open(cache_path, 'w') as file:
                json.dump(entries, file, indent=2)

    if skip_deprecated:
        entries = [
            entry
            for entry in entries
            if not entry.get('is_obsolete', False)
        ]

    if mappify:
        entries = list_to_map(entries, 'id')

    return entries


@click.command()
def main():
    """Reload the OBO Foundry data."""
    get_obofoundry(force_download=True)


if __name__ == '__main__':
    main()
