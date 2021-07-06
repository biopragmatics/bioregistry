# -*- coding: utf-8 -*-

"""Command line interface for the bioregistry."""

import click

from .bioportal import get_bioportal
from .go import get_go
from .miriam import get_miriam
from .n2t import get_n2t
from .ncbi import get_ncbi
from .obofoundry import get_obofoundry
from .ols import get_ols
from .wikidata import get_wikidata
from ..utils import secho

__all__ = [
    "download",
]


@click.command()
def download():
    """Download/update the external entries in the Bioregistry."""
    secho("Downloading MIRIAM")
    get_miriam(force_download=True)

    secho("Download N2T")
    get_n2t(force_download=True)

    secho("Downloading NCBI")
    get_ncbi(force_download=True)

    secho("Downloading OBO Foundry")
    get_obofoundry(force_download=True)

    secho("Downloading OLS")
    get_ols(force_download=True)

    secho("Download Wikidata")
    get_wikidata(force_download=True)

    secho("Download GO")
    get_go(force_download=True)

    secho("Download BioPortal")
    get_bioportal(force_download=True)


if __name__ == "__main__":
    download()
