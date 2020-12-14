# -*- coding: utf-8 -*-

"""Command line interface for the bioregistry."""

import click

from .align.cli import align
from .external.cli import download
from .lint import lint


@click.group()
def main():
    """Run the Bioregistry CLI."""


main.add_command(lint)


@main.command()
@click.pass_context
def update(ctx: click.Context):
    """Update the Bioregistry."""
    ctx.invoke(download)
    ctx.invoke(align)
    ctx.invoke(lint)


if __name__ == '__main__':
    main()
