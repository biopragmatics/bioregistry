# -*- coding: utf-8 -*-

"""Command line interface for the bioregistry."""

import os

import click
import yaml

from .align.cli import align
from .external.cli import download
from .lint import lint


@click.group()
def main():
    """Run the Bioregistry CLI."""


main.add_command(lint)


@main.command()
def copy():
    """Copy the source Bioregistry to the docs folder."""
    here = os.path.abspath(os.path.dirname(__file__))
    data = os.path.abspath(os.path.join(here, os.pardir, os.pardir, 'docs', '_data', 'bioregistry.yml'))
    from . import read_bioregistry

    registry = read_bioregistry()
    ov = [
        {
            'prefix': prefix,
            **data,
        }
        for prefix, data in registry.items()
    ]
    with open(data, 'w') as file:
        yaml.dump(ov, file)


@main.command()
@click.pass_context
def update(ctx: click.Context):
    """Update the Bioregistry."""
    ctx.invoke(download)
    ctx.invoke(align)
    ctx.invoke(lint)
    ctx.invoke(copy)


if __name__ == '__main__':
    main()
