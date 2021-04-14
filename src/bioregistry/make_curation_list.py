# -*- coding: utf-8 -*-

"""Make the curation list."""

import os

import click
import yaml

import bioregistry
from bioregistry.constants import DOCS_DATA

items = sorted(bioregistry.read_registry().items())


def _g(predicate):
    return [
        {
            'prefix': bioregistry_id,
            'name': bioregistry.get_name(bioregistry_id),
        }
        for bioregistry_id, bioregistry_entry in items
        if predicate(bioregistry_id, bioregistry_entry)
    ]


@click.command()
def curation():
    """Make curation list."""
    missing_wikidata_database = _g(lambda prefix, entry: entry.get('wikidata', {}).get('database') is None)
    missing_pattern = _g(lambda prefix, entry: bioregistry.get_pattern(prefix) is None)
    missing_format_url = _g(lambda prefix, entry: bioregistry.get_format(prefix) is None)
    missing_example = _g(lambda prefix, entry: bioregistry.get_example(prefix) is None)

    with open(os.path.join(DOCS_DATA, 'curation.yml'), 'w') as file:
        yaml.safe_dump(
            {
                'wikidata': missing_wikidata_database,
                'pattern': missing_pattern,
                'formatter': missing_format_url,
                'example': missing_example,
            },
            file,
        )


if __name__ == '__main__':
    curation()
