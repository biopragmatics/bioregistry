# -*- coding: utf-8 -*-

"""Upgrade the prefixes in the @context of the JSON-LD file."""

import json
import sys
from textwrap import dedent

import click

import bioregistry


@click.command()
@click.option('--file', type=click.File('r'), default=sys.stdin)
@click.option('--output', type=click.File('w'), default=sys.stdout)
@click.option('--indent', type=int, default=2)
@click.option('--sort-keys', is_flag=True)
def main(file, output, indent: int, sort_keys: bool):
    """Upgrade the prefixes in the @context of the JSON-LD file."""
    rv = json.load(file)
    rv = upgrade_jsonld_context(rv)
    json.dump(rv, output, indent=indent, sort_keys=sort_keys)


def upgrade_jsonld_context(d):
    """Upgrade the prefixes in @context of the JSON-LD object in place."""
    rv = {}
    unnorm = []
    for prefix, value in d['@context'].items():
        norm_prefix = bioregistry.normalize_prefix(prefix)
        if norm_prefix is None:
            click.secho(f'Could not normalize prefix {prefix}.')
            unnorm.append(prefix)
        else:
            rv[prefix] = value
    if unnorm:
        click.secho(dedent(f'''\
        Unable to normalize {len(unnorm)} prefixes.

        Please consider opening an issue on https://github.com/bioregistry/bioregistry/issues.
        '''))
    d['@context'] = rv
    return d


if __name__ == '__main__':
    main()
