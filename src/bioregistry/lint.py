# -*- coding: utf-8 -*-

"""Linting functions."""

import click

from bioregistry.utils import secho, updater


@updater
def warn_missing_wikidata(registry):
    """Write warnings for entries completely missing a Wikidata property, database, or paper."""
    _warn_missing_key(registry, 'wikidata')


def _warn_missing_key(registry, key):
    prefixes = [
        prefix
        for prefix, entry in registry.items()
        if key not in entry
    ]
    if prefixes:
        secho(f'Missing {key}:')
        for prefix in prefixes:
            click.echo(f'{prefix:15}: {_get_key(registry, prefix, "name")}')


def _get_key(registry, prefix, key):
    return (
        registry[prefix].get(key)
        or registry[prefix].get("miriam", {}).get(key)
        or registry[prefix].get("obofoundry", {}).get(key)
        or registry[prefix].get("ols", {}).get(key)
        or registry[prefix].get("wikidata", {}).get(key)
        or ''
    )


@updater
def sort_registry(registry):
    """Sort the registry."""
    return registry


@click.command()
def lint():
    """Run the lint commands."""
    warn_missing_wikidata()
    sort_registry()


if __name__ == '__main__':
    lint()
