# -*- coding: utf-8 -*-

"""Command line interface for the bioregistry."""

import click

from .bioportal import get_bioportal
from .go import get_go
from .miriam import get_miriam_df
from .n2t import get_n2t
from .ncbi import get_ncbi
from .obofoundry import get_obofoundry_df
from .ols import get_ols_df
from .wikidata import get_wikidata_registry
from ..utils import secho

__all__ = [
    'download',
]


@click.command()
def download():
    """Download/update the external entries in the Bioregistry."""
    secho('Downloading MIRIAM')
    get_miriam_df(force_download=True)

    secho('Download N2T')
    get_n2t()

    secho('Downloading NCBI')
    get_ncbi()

    secho('Downloading OBO Foundry')
    get_obofoundry_df(force_download=True)

    secho('Downloading OLS')
    get_ols_df(force_download=True)

    secho('Download Wikidata')
    get_wikidata_registry()

    secho('Download GO')
    get_go(force_download=True)

    secho('Download BioPortal')
    get_bioportal(force_download=True)


if __name__ == '__main__':
    download()
