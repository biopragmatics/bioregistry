# -*- coding: utf-8 -*-

"""Download the Gene Ontology registry."""

import json
import os
from typing import Optional

import click
import yaml

from bioregistry.constants import BIOREGISTRY_MODULE
from bioregistry.external.utils import list_to_map

__all__ = [
    'GO_FULL_PATH',
    'GO_URL',
    'get_go',
]

# Xrefs from GO that aren't generally useful
SKIP = {
    'TO_GIT',
    'OBO_SF_PO',
    'OBO_SF2_PO',
    'OBO_SF2_PECO',
    'PECO_GIT',
    'PO_GIT',
    'PSO_GIT',
    'EO_GIT',
}

# The key is redundant of the value
REDUNDANT = {
    "AspGD": "AspGD_LOCUS",
}

GO_YAML_PATH = BIOREGISTRY_MODULE.join(name='go.yml')
GO_FULL_PATH = BIOREGISTRY_MODULE.join(name='go.json')
GO_URL = 'https://raw.githubusercontent.com/geneontology/go-site/master/metadata/db-xrefs.yaml'


def get_go(
    cache_path: Optional[str] = GO_FULL_PATH,
    mappify: bool = False,

    force_download: bool = False,
):
    """Get the GO registry."""
    if not force_download and cache_path is not None and os.path.exists(cache_path):
        with open(cache_path) as file:
            entries = json.load(file)
    else:
        with BIOREGISTRY_MODULE.ensure(url=GO_URL).open() as file:
            entries = yaml.full_load(file)
        entries = [
            entry
            for entry in entries
            if entry['database'] not in SKIP and entry['database'] not in REDUNDANT
        ]
        if cache_path is not None:
            with open(cache_path, 'w') as file:
                json.dump(entries, file, indent=2, sort_keys=True)

    if mappify:
        entries = list_to_map(entries, 'database')

    return entries


@click.command()
def main():
    """Reload the GO data."""
    get_go(force_download=True)


if __name__ == '__main__':
    main()
