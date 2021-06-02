# -*- coding: utf-8 -*-

"""Command line interface for the bioregistry."""

import os

import click
import yaml
from more_click import make_web_command

from bioregistry import read_collections, read_metaregistry
from . import resolve
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
def export():
    """Copy the source Bioregistry to the docs folder."""
    from .utils import read_registry
    registry = read_registry()

    # YAML - registry
    ov = [
        {
            'prefix': prefix,
            **data,
        }
        for prefix, data in registry.items()
    ]
    with open(os.path.join(DOCS_DATA, 'bioregistry.yml'), 'w') as file:
        yaml.dump(ov, file)

    import pandas as pd
    rows = []
    for identifier, data in read_collections().items():
        rows.append((
            identifier,
            data['name'],
            data['description'],
            '|'.join(data['resources']),
            '|'.join(e['name'] for e in data['authors']),
            '|'.join(e['orcid'] for e in data['authors']),
        ))
    df = pd.DataFrame(rows, columns=['identifier', 'name', 'description', 'resources', 'author_names', 'author_orcids'])
    df.to_csv(os.path.join(DOCS_DATA, 'collections.tsv'), index=False, sep='\t')

    df = pd.DataFrame.from_dict(dict(read_metaregistry()), orient='index')
    df.index.name = 'metaprefix'
    df.to_csv(os.path.join(DOCS_DATA, 'metaregistry.tsv'), sep='\t')

    metaprefixes = [
        k
        for k in sorted(read_metaregistry())
        if k not in {'bioregistry', 'biolink', 'ncbi', 'fairsharing', 'go'}
    ]

    rows = []
    for prefix, data in read_registry().items():
        mappings = resolve.get_mappings(prefix)
        rows.append((
            prefix,
            resolve.get_name(prefix),
            resolve.get_homepage(prefix),
            resolve.get_description(prefix),
            resolve.get_pattern(prefix),
            resolve.get_example(prefix),
            resolve.get_email(prefix),
            resolve.get_format(prefix),
            data.get('download'),
            '|'.join(data.get('synonyms', [])),
            data.get('deprecated', False),
            *[
                mappings.get(metaprefix)
                for metaprefix in metaprefixes
            ],
            '|'.join(data.get('appears_in', [])),
            data.get('part_of'),
            data.get('provides'),
            data.get('type'),
            # TODO could add more, especially mappings
        ))

    df = pd.DataFrame(rows, columns=[
        'identifier', 'name', 'homepage', 'description', 'pattern',
        'example', 'email', 'formatter', 'download', 'synonyms',
        'deprecated', *metaprefixes, 'appears_in', 'part_of', 'provides', 'type',
    ])
    df.to_csv(os.path.join(DOCS_DATA, 'bioregistry.tsv'), index=False, sep='\t')


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
    ctx.invoke(exports)
    ctx.invoke(compare)
    ctx.invoke(curation)
    ctx.invoke(warnings)
    ctx.invoke(generate_context_json_ld)


if __name__ == '__main__':
    main()
