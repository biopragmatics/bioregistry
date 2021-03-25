# -*- coding: utf-8 -*-

"""Query, download, and format Wikidata as a registry."""

import logging
from typing import Iterable, Tuple

import pandas as pd

from bioregistry.constants import BIOREGISTRY_MODULE
from bioregistry.external.miriam import get_miriam
from bioregistry.utils import query_wikidata

logger = logging.getLogger(__name__)

DATABASES_PATH = BIOREGISTRY_MODULE.join(name='wikidata_databases.tsv')
MIRIAM_PATH = BIOREGISTRY_MODULE.join(name='wikidata_miriam.tsv')


def get_database() -> pd.DataFrame:
    """Get the databases dataframe."""
    df = pd.DataFrame(iter_database(), columns=['database_id', 'database_label', 'prop_id', 'prop_label'])
    df.to_csv(DATABASES_PATH, sep='\t', index=False)
    return df


def iter_database() -> Iterable[Tuple[str, str, str, str]]:
    """Iterate over database-property pairs from Wikidata."""
    query = """
    SELECT ?database ?databaseLabel ?prop ?propLabel
    WHERE
    {
      ?database wdt:P31 wd:Q4117139 .
      ?database wdt:P1687 ?prop .
      SERVICE wikibase:label { bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en". }
    }
    """
    for d in query_wikidata(query):
        database_id = d['database']['value'].split('/')[-1]
        database_label = d['databaseLabel']['value']
        prop_id = d['prop']['value'].split('/')[-1]
        prop_label = d['propLabel']['value']
        yield database_id, database_label, prop_id, prop_label


def get_miriam_mappings() -> pd.DataFrame:
    """Get MIRIAM-Wikidata mappings."""
    df = pd.DataFrame(iter_wikidata_mappings(), columns=['prop_id', 'prop_label', 'miriam_id', 'miriam_label'])
    df.to_csv(MIRIAM_PATH, sep='\t', index=False)
    return df


def iter_wikidata_mappings() -> Iterable[Tuple[str, str, str, str]]:
    """Iterate over Wikidata xrefs."""
    miriam = get_miriam(mappify=True)

    query = """SELECT ?item ?itemLabel ?miriam
    WHERE
    {
      ?item wdt:P4793 ?miriam .
      SERVICE wikibase:label { bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en". }
    }
    """
    # P4793 identifiers.org prefix
    #

    wikidata_to_miriam = {
        'wormbase': 'wb',
        'flybase': 'fb',
    }

    for d in query_wikidata(query):
        wikidata_id = d['item']['value'].split('/')[-1]
        wikidata_label = d['itemLabel']['value']
        miriam_label = d['miriam']['value'].lower()
        miriam_label = wikidata_to_miriam.get(miriam_label, miriam_label)

        miriam_entry = miriam.get(miriam_label)
        if miriam_entry is None:
            logger.debug('MISSING %s %s %s', wikidata_id, wikidata_label, miriam_label)
            continue

        miriam_id = miriam_entry['mirId'].removeprefix('MIR:')
        yield wikidata_id, wikidata_label, miriam_id, miriam_label


def get_wikidata_registry():
    """Get the wikidata registry."""
    m = get_miriam_mappings()
    get_database()
    return set(m['miriam_label'])


if __name__ == '__main__':
    get_wikidata_registry()
