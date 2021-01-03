# -*- coding: utf-8 -*-

"""Linting functions."""

import click

from .utils import clean_set, secho, updater


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


@click.command()
def lint():
    """Run the lint commands."""
    warn_missing_wikidata()


if __name__ == '__main__':
    lint()


@updater
def cleanup_synonyms(registry):
    """Remove redundant synonyms and empty synonym dictionaries."""
    for key, entry in registry.items():
        if 'synonyms' not in entry:
            continue

        skip_synonyms = clean_set(key, *[
            entry.get(k, {}).get('name')
            for k in ['miriam', 'ols', 'obofoundry']
        ])

        entry['synonyms'] = [synonym for synonym in entry['synonyms'] if synonym not in skip_synonyms]
        if 0 == len(entry['synonyms']):
            del entry['synonyms']
