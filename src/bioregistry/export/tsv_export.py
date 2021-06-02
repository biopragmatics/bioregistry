# -*- coding: utf-8 -*-

"""Export components of the bioregistry to TSV."""

import os

import click

from bioregistry import read_collections, read_metaregistry
from .. import resolve
from ..constants import DOCS_DATA
from ..utils import read_registry


@click.command()
def export_tsv():
    """Export TSV."""
    get_collections_df().to_csv(os.path.join(DOCS_DATA, 'collections.tsv'), index=False, sep='\t')
    get_metaregistry_df().to_csv(os.path.join(DOCS_DATA, 'metaregistry.tsv'), sep='\t')
    get_registry_df().to_csv(os.path.join(DOCS_DATA, 'registry.tsv'), index=False, sep='\t')


def get_collections_df():
    """Get a dataframe of all collections."""
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

    import pandas as pd
    df = pd.DataFrame(rows, columns=['identifier', 'name', 'description', 'resources', 'author_names', 'author_orcids'])
    return df


def get_metaregistry_df():
    """Get a dataframe of all metaresources."""
    import pandas as pd
    df = pd.DataFrame.from_dict(dict(read_metaregistry()), orient='index')
    df.index.name = 'metaprefix'
    return df


def get_registry_df():
    """Get a dataframe of all resources."""
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
            resolve.is_deprecated(prefix),
            *[
                mappings.get(metaprefix)
                for metaprefix in metaprefixes
            ],
            # '|'.join(data.get('appears_in', [])),
            data.get('part_of'),
            data.get('provides'),
            data.get('type'),
            # TODO could add more, especially mappings
        ))

    import pandas as pd
    df = pd.DataFrame(rows, columns=[
        'identifier', 'name', 'homepage', 'description', 'pattern',
        'example', 'email', 'formatter', 'download', 'synonyms',
        'deprecated', *metaprefixes, 'appears_in', 'part_of', 'provides', 'type',
    ])
    return df


if __name__ == '__main__':
    export_tsv()
