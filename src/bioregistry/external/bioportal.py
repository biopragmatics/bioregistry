# -*- coding: utf-8 -*-

"""Download the NCBO BioPortal registry.

Get an API key by logging up, signing in, and navigating to https://bioportal.bioontology.org/account.
"""

import json

import click
import pystow
import requests
from more_click import verbose_option

from bioregistry.constants import BIOREGISTRY_MODULE
from bioregistry.external.utils import list_to_map

BIOPORTAL_PATH = BIOREGISTRY_MODULE.get('bioportal.json')
BIOPORTAL_API_KEY = pystow.get_config('bioportal', 'api_key')
BASE_URL = 'https://data.bioontology.org'


def query(url: str, **params) -> requests.Response:
    """Query the given endpoint on BioPortal."""
    params.setdefault('apikey', BIOPORTAL_API_KEY)
    return requests.get(f'{BASE_URL}/{url}', params=params)


def get_bioportal(force: bool = True, mappify: bool = False):
    """Get the BioPortal registry."""
    if BIOPORTAL_PATH.exists() and not force:
        with BIOPORTAL_PATH.open() as file:
            entries = json.load(file)
    else:
        # see https://data.bioontology.org/documentation#Ontology
        res = query('ontologies', summaryOnly=False, notes=True)
        entries = res.json()
        for entry in entries:
            for key in ('links', '@context'):
                if key in entry:
                    del entry[key]

        with BIOPORTAL_PATH.open('w') as file:
            json.dump(entries, file, indent=2)

    if mappify:
        entries = list_to_map(entries, 'acronym')

    return entries


@click.command()
@verbose_option
def _main():
    get_bioportal()


if __name__ == '__main__':
    _main()
