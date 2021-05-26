# -*- coding: utf-8 -*-

"""Export the Bioregistry as a JSON-LD context."""

import json
import logging
from pathlib import Path
from typing import Mapping

import click

import bioregistry
from bioregistry.constants import DOCS_DATA

logger = logging.getLogger(__name__)


@click.command()
def generate_context_json_ld():
    """Generate various JSON-LD context files."""
    contexts_directory = Path(DOCS_DATA) / 'contexts'
    contexts_directory.mkdir(parents=True, exist_ok=True)

    with contexts_directory.joinpath('obo_context.jsonld').open('w') as file:
        json.dump(fp=file, indent=4, sort_keys=True, obj={
            "@context": get_obofoundry_prefix_map(),
        })

    for key, collection in bioregistry.read_collections().items():
        name = collection.get('contextName')
        if name is None:
            continue
        with contexts_directory.joinpath(f'{name}_context').with_suffix('.jsonld').open('w') as file:
            json.dump(fp=file, indent=4, sort_keys=True, obj={
                "@context": get_collection_prefix_map(key),
            })


def get_collection_prefix_map(key: str) -> Mapping[str, str]:
    """Get a prefix map for a given collection."""
    rv = {}
    for prefix in bioregistry.read_collections()[key]['resources']:
        fmt = bioregistry.get_format(prefix)
        if fmt is None:
            logging.warning('collection term missing formatter: %s', prefix)
            continue
        if not fmt.endswith('$1'):
            logging.warning('formatter missing $1: %s', prefix)
            continue
        if fmt.count('$1') != 1:
            logging.warning('formatter has multiple $1: %s', prefix)
            continue
        rv[prefix] = fmt[:-len('$1')]
    return rv


def get_obofoundry_prefix_map() -> Mapping[str, str]:
    """Get the OBO foundry prefix map."""
    rv = {}
    for prefix in bioregistry.read_registry():
        obofoundry_prefix = bioregistry.get_obofoundry_prefix(prefix)
        obofoundry_fmt = bioregistry.get_obofoundry_format(prefix)
        if obofoundry_prefix is None or obofoundry_fmt is None:
            continue
        rv[obofoundry_prefix] = obofoundry_fmt
    return rv


if __name__ == '__main__':
    generate_context_json_ld()
