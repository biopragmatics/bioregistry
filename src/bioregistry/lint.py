# -*- coding: utf-8 -*-

"""Linting functions."""

import click

from .utils import updater


@updater
def warn_missing_name(registry):
    """Write warnings for entries that are missing a name."""
    prefixes = [
        prefix
        for prefix, entry in registry.items()
        if (
            'name' not in entry
            and 'name' not in entry.get('miriam', {})
            and 'name' not in entry.get('ols', {})
            and 'name' not in entry.get('obofoundry', {})
        )
    ]
    if prefixes:
        click.secho('Missing titles:', fg='cyan', bold=True)
        for prefix in prefixes:
            click.echo(prefix)


@updater
def warn_missing_entry(registry):
    """Write warnings for entries completely missing content."""
    prefixes = [
        prefix
        for prefix, entry in registry.items()
        if not entry
    ]
    if prefixes:
        click.secho('Missing entry:', fg='cyan', bold=True)
        for prefix in prefixes:
            click.echo(prefix)


@click.command()
def lint():
    """Run the lint commands."""
    warn_missing_entry()
    warn_missing_name()


if __name__ == '__main__':
    lint()
