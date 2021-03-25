# -*- coding: utf-8 -*-

"""Download registry information from Identifiers.org/MIRIAMs."""

from typing import Optional

import click
import pandas as pd

from .utils import ensure_registry
from ..constants import BIOREGISTRY_MODULE

__all__ = [
    'MIRIAM_FULL_PATH',
    'MIRIAM_URL',
    'get_miriam',
    'get_miriam_df',
]

MIRIAM_FULL_PATH = BIOREGISTRY_MODULE.join(name='miriam.json')
MIRIAM_SLIM_PATH = BIOREGISTRY_MODULE.join(name='miriam.tsv')
MIRIAM_URL = 'https://registry.api.identifiers.org/restApi/namespaces'


def get_miriam(
    cache_path: Optional[str] = MIRIAM_FULL_PATH,
    mappify: bool = False,
    force_download: bool = False,
    skip_deprecated: bool = False,
):
    """Get the MIRIAM registry."""
    return ensure_registry(
        url=MIRIAM_URL,
        embedded_key='namespaces',
        cache_path=cache_path,
        id_key='prefix',
        mappify=mappify,
        force_download=force_download,
        deprecated_key='deprecated',
        skip_deprecated=skip_deprecated,
    )


def get_miriam_df(**kwargs):
    """Get the MIRIAM registry as a pre-processed dataframe."""
    rows = [
        (
            'miriam',
            entry['mirId'],
            entry['prefix'],
            entry['pattern'],
            entry['namespaceEmbeddedInLui'],
            entry['name'],
            entry['deprecated'],
            entry['description'],
            entry['sampleId'],
        )
        for entry in get_miriam(**kwargs)
    ]
    df = pd.DataFrame(rows, columns=[
        'registry', 'identifier', 'prefix',
        'pattern', 'namespaceEmbeddedInLui', 'name', 'deprecated', 'description', 'sampleId',
    ])
    df.to_csv(MIRIAM_SLIM_PATH, sep='\t', index=False)
    return df


@click.command()
def main():
    """Reload the MIRIAM data."""
    get_miriam_df(force_download=True)


if __name__ == '__main__':
    main()
