# -*- coding: utf-8 -*-

"""Command line interface for the bioregistry."""

import sys

import click

from ..utils import secho

__all__ = [
    "download",
]


@click.command()
def download():
    """Download/update the external entries in the Bioregistry."""
    try:
        from bioregistry.external.getters import GETTERS
    except ImportError:
        click.secho(
            "Could not import alignment dependencies."
            " Install bioregistry again with `pip install bioregistry[align]`.",
            fg="red",
        )
        return sys.exit(1)

    for _, name, getter in GETTERS:
        secho(f"Downloading {name}")
        getter(force_download=True)


if __name__ == "__main__":
    download()
