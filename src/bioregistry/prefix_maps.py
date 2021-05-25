# -*- coding: utf-8 -*-

"""Export the Bioregistry as a JSON-LD context."""

import json
from pathlib import Path
from typing import Mapping

import click

import bioregistry
from bioregistry.constants import DOCS_DATA


@click.command()
def generate_context_json_ld():
    """Generate various JSON-LD context files."""
    contexts_directory = Path(DOCS_DATA) / 'contexts'
    contexts_directory.mkdir(parents=True, exist_ok=True)

    with contexts_directory.joinpath('obo_context.jsonld').open('w') as file:
        json.dump(fp=file, indent=4, sort_keys=True, obj={
            "@context": get_obofoundry_prefix_map(),
        })


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
