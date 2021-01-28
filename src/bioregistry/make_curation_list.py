# -*- coding: utf-8 -*-

"""Make the curation list."""

import os

import click
import yaml

from bioregistry import get_name, read_bioregistry
from bioregistry.constants import DOCS_DATA


@click.command()
def curation():
    """Make curation list."""
    wikidata = [
        {
            'prefix': bioregistry_id,
            'name': get_name(bioregistry_id),
            **bioregistry_entry,
        }
        for bioregistry_id, bioregistry_entry in read_bioregistry().items()
        if bioregistry_entry.get('wikidata', {}).get('database') is None
    ]

    with open(os.path.join(DOCS_DATA, 'curation.yml'), 'w') as file:
        yaml.safe_dump(
            {
                'wikidata': wikidata,
            },
            file,
        )


if __name__ == '__main__':
    curation()
