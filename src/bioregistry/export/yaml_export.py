# -*- coding: utf-8 -*-

"""Export components of the bioregistry to YAML."""

import os

import click
import yaml

from ..constants import DOCS_DATA
from ..utils import read_registry


@click.command()
def export_yaml():
    """Export the registry as YAML."""
    registry = read_registry()

    # YAML - registry
    ov = [
        {
            'prefix': prefix,
            **data,
        }
        for prefix, data in registry.items()
    ]
    with open(os.path.join(DOCS_DATA, 'registry.yml'), 'w') as file:
        yaml.dump(ov, file)


if __name__ == '__main__':
    export_yaml()
