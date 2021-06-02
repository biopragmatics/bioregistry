# -*- coding: utf-8 -*-

"""Download registry information from the OLS."""

from typing import Optional

import click

from .utils import ensure_registry
from ..constants import BIOREGISTRY_MODULE

__all__ = [
    'OLS_FULL_PATH',
    'OLS_URL',
    'get_ols',
]

OLS_URL = 'http://www.ebi.ac.uk/ols/api/ontologies'
OLS_FULL_PATH = BIOREGISTRY_MODULE.join(name='ols.json')


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


@click.command()
def main():
    """Reload the OLS data."""
    get_ols(force_download=True)


if __name__ == '__main__':
    main()
