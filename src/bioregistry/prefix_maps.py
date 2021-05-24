# -*- coding: utf-8 -*-

"""Export the Bioregistry as a JSON-LD context."""

import json
from pathlib import Path
from typing import Mapping

import click

import bioregistry
from bioregistry.constants import DOCS_DATA


@click.command()
def main():
    contexts_directory = Path(DOCS_DATA) / 'contexts'
    contexts_directory.mkdir(parents=True, exist_ok=True)

    obofoundry_context = contexts_directory / 'obo_context.jsonld'
    with obofoundry_context.open('w') as file:
        json.dump(fp=file, indent=4, sort_keys=True, obj=_generate_context_json_ld(get_obofoundry_prefix_map()))


def _generate_context_json_ld(prefix_map: Mapping[str, str]) -> Mapping[str, Mapping[str, str]]:
    """Convert a prefix map into a JSON-LD context JSON"""
    return {"@context": prefix_map}


def get_obofoundry_prefix_map() -> Mapping[str, str]:
    rv = {}
    for prefix in bioregistry.read_registry():
        obofoundry_prefix = bioregistry.get_obofoundry_prefix(prefix)
        if obofoundry_prefix is None:
            continue
        rv[obofoundry_prefix] = f'http://purl.obolibrary.org/obo/{obofoundry_prefix.upper()}_'
    return rv


def _best():
    rv = {}
    for prefix in bioregistry.read_registry():
        fmt = bioregistry.get_format(prefix)
        if not fmt:
            continue
        if fmt.count('$1') > 1:
            print('problem', prefix, fmt)
            continue
        if not fmt.endswith('$1'):
            print('problem', prefix, fmt)
            continue
        rv[prefix] = fmt
    return rv


if __name__ == '__main__':
    main()
