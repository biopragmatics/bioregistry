# -*- coding: utf-8 -*-

"""Command line interface for the bioregistry."""

import click

from .external.miriam import get_miriam_df
from .external.obofoundry import get_obofoundry_df
from .external.ols import get_ols_df


@click.group()
def main():
    """Run the Bioregistry CLI."""


@click.command()
def update():
    """Update the Bioregistry."""
    get_miriam_df(force_download=True)
    get_ols_df(force_download=True)
    get_obofoundry_df(force_download=True)


if __name__ == '__main__':
    main()
