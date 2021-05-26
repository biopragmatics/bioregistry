# -*- coding: utf-8 -*-

"""Download registry information from Identifiers.org/MIRIAMs."""

from typing import Optional

import click

from .utils import ensure_registry
from ..constants import BIOREGISTRY_MODULE

__all__ = [
    'MIRIAM_FULL_PATH',
    'MIRIAM_URL',
    'get_miriam',
]

MIRIAM_FULL_PATH = BIOREGISTRY_MODULE.join(name='miriam.json')
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


@click.command()
def main():
    """Reload the MIRIAM data."""
    get_miriam(force_download=True)


if __name__ == '__main__':
    main()
