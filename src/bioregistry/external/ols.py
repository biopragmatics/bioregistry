# -*- coding: utf-8 -*-

"""Download registry information from the OLS."""

from typing import Optional

import click
import pandas as pd

from .utils import ensure_registry
from ..constants import BIOREGISTRY_MODULE

__all__ = [
    'OLS_FULL_PATH',
    'OLS_URL',
    'get_ols',
    'get_ols_df',
]

OLS_URL = 'http://www.ebi.ac.uk/ols/api/ontologies'
OLS_FULL_PATH = BIOREGISTRY_MODULE.join(name='ols.json')
OLS_SLIM_PATH = BIOREGISTRY_MODULE.join(name='ols.tsv')


def get_ols(cache_path: Optional[str] = OLS_FULL_PATH, mappify: bool = False, force_download: bool = False):
    """Get the OLS registry."""
    return ensure_registry(
        url=OLS_URL,
        embedded_key='ontologies',
        cache_path=cache_path,
        id_key='ontologyId',
        mappify=mappify,
        force_download=force_download,
    )


def get_ols_df(**kwargs):
    """Get the OLS registry as a pre-processed dataframe."""
    rows = [
        (
            'ols',
            entry['ontologyId'],
            entry['config']['title'],
            entry['config']['annotations'].get('description'),
            entry['config']['annotations'].get('license', [None])[0],
            entry.get('version'),
        )
        for entry in get_ols(**kwargs)
    ]
    df = pd.DataFrame(rows, columns=[
        'registry', 'prefix', 'name', 'description', 'license', 'version',
    ])
    df.to_csv(OLS_SLIM_PATH, sep='\t', index=False)
    return df


@click.command()
def main():
    """Reload the OLS data."""
    get_ols_df(force_download=True)


if __name__ == '__main__':
    main()
