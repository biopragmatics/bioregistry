# -*- coding: utf-8 -*-

"""Command line interface for the bioregistry."""

import os

import click
import yaml
from more_click import make_web_command

from .align.cli import align
from .compare import compare
from .constants import DOCS_DATA
from .external.cli import download
from .generate_warnings_file import warnings
from .lint import lint
from .make_curation_list import curation
from .prefix_maps import generate_context_json_ld
from .version import VERSION


@click.group()
@click.version_option(version=VERSION)
def main():
    """Run the Bioregistry CLI."""


main.add_command(lint)
main.add_command(compare)
main.add_command(warnings)
main.add_command(make_web_command('bioregistry.app.wsgi:app'))


@main.command()
def copy():
    """Copy the source Bioregistry to the docs folder."""
    from .utils import read_registry
    registry = read_registry()
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
def versions():
    """Print the versions."""
    from .utils import read_registry
    from .resolve import get_versions
    from tabulate import tabulate

    registry = read_registry()
    click.echo(tabulate(
        [
            (k, v)
            for k, v in sorted(get_versions().items())
            if "ols_version_date_format" not in registry[k] and "ols_version_type" not in registry[k]
        ],
        headers=['Prefix', 'Version'],
    ))


@main.command()
@click.pass_context
def update(ctx: click.Context):
    """Update the Bioregistry."""
    ctx.invoke(download)
    ctx.invoke(align)
    ctx.invoke(lint)
    ctx.invoke(copy)
    ctx.invoke(compare)
    ctx.invoke(curation)
    ctx.invoke(warnings)
    ctx.invoke(generate_context_json_ld)


if __name__ == '__main__':
    main()
