# -*- coding: utf-8 -*-

"""Make the curation list."""

import copy
import os

import click
import yaml

from bioregistry import get_name, get_pattern, read_bioregistry
from bioregistry.constants import DOCS_DATA


@click.command()
def curation():
    """Make curation list."""
    items = sorted(read_bioregistry().items())
    missing_wikidata_database = [
        {
            'prefix': bioregistry_id,
            'name': get_name(bioregistry_id),
            **bioregistry_entry,
        }
        for bioregistry_id, bioregistry_entry in items
        if bioregistry_entry.get('wikidata', {}).get('database') is None
    ]

    missing_pattern = [
        {
            'prefix': bioregistry_id,
            'name': get_name(bioregistry_id),
            **bioregistry_entry,
        }
        for bioregistry_id, bioregistry_entry in items
        if get_pattern(bioregistry_id)
    ]

    with open(os.path.join(DOCS_DATA, 'curation.yml'), 'w') as file:
        yaml.safe_dump(
            {
                'wikidata': copy.deepcopy(missing_wikidata_database),
                'pattern': copy.deepcopy(missing_pattern),
            },
            file,
        )


if __name__ == '__main__':
    curation()
