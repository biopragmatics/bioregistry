# -*- coding: utf-8 -*-

"""Command line interface for the bioregistry."""

import click
from more_click import make_web_command

from .align.cli import align
from .compare import compare
from .curation.wikidata_curation import main as wikidata_curation
from .export.cli import export
from .external.cli import download
from .generate_warnings_file import warnings
from .lint import lint
from .version import VERSION


@click.group()
@click.version_option(version=VERSION)
def main():
    """Run the Bioregistry CLI."""


main.add_command(lint)
main.add_command(compare)
main.add_command(warnings)
main.add_command(export)
main.add_command(download)
main.add_command(align)
main.add_command(make_web_command("bioregistry.app.wsgi:app"))


@main.command()
def versions():
    """Print the versions."""
    from .resolve import get_versions
    from tabulate import tabulate

    click.echo(
        tabulate(
            sorted(get_versions().items()),
            headers=["Prefix", "Version"],
        )
    )


@main.command()
@click.pass_context
def update(ctx: click.Context):
    """Update the Bioregistry."""
    ctx.invoke(align)
    ctx.invoke(lint)
    ctx.invoke(export)
    ctx.invoke(compare)
    ctx.invoke(wikidata_curation)
    ctx.invoke(warnings)


if __name__ == "__main__":
    main()
