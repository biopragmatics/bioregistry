# -*- coding: utf-8 -*-

"""Export components of the bioregistry to YAML."""

import os

import click
import yaml

from ..constants import DOCS_DATA
from ..utils import read_collections, read_metaregistry, read_registry


@click.command()
def export_yaml():
    """Export the registry as YAML."""
    with open(os.path.join(DOCS_DATA, 'registry.yml'), 'w') as file:
        yaml.dump(stream=file, data=[
            {
                'prefix': prefix,
                **data,
            }
            for prefix, data in read_registry().items()
        ])
    with open(os.path.join(DOCS_DATA, 'metaregistry.yml'), 'w') as file:
        yaml.dump(stream=file, data=read_metaregistry())
    with open(os.path.join(DOCS_DATA, 'collections.yml'), 'w') as file:
        yaml.dump(stream=file, data=read_collections())


if __name__ == '__main__':
    export_yaml()
