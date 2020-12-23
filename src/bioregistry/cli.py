# -*- coding: utf-8 -*-

"""Command line interface for the bioregistry."""

import os

import click
import yaml

from .align.cli import align
from .compare import compare
from .constants import DOCS_DATA
from .external.cli import download
from .lint import lint


@click.group()
def main():
    """Run the Bioregistry CLI."""


main.add_command(lint)
main.add_command(compare)


@main.command()
def copy():
    """Copy the source Bioregistry to the docs folder."""
    from . import read_bioregistry
    registry = read_bioregistry()
    ov = [
        {
            'prefix': prefix,
            **data,
        }
        for prefix, data in registry.items()
    ]
    with open(os.path.join(DOCS_DATA, 'bioregistry.yml'), 'w') as file:
        yaml.dump(ov, file)


@main.command()
@click.pass_context
def update(ctx: click.Context):
    """Update the Bioregistry."""
    ctx.invoke(download)
    ctx.invoke(align)
    ctx.invoke(lint)
    ctx.invoke(copy)
    ctx.invoke(compare)


if __name__ == '__main__':
    main()
