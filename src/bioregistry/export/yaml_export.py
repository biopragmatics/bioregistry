# -*- coding: utf-8 -*-

"""Export components of the bioregistry to YAML."""

import os

import click
import yaml

from ..constants import DOCS_DATA
from ..schema import sanitize_mapping
from ..utils import read_collections, read_metaregistry, read_registry


@click.command()
def export_yaml():
    """Export the registry as YAML."""
    with open(os.path.join(DOCS_DATA, "registry.yml"), "w") as file:
        yaml.dump(stream=file, data=sanitize_mapping(read_registry()))
    with open(os.path.join(DOCS_DATA, "metaregistry.yml"), "w") as file:
        yaml.dump(stream=file, data=sanitize_mapping(read_metaregistry()))
    with open(os.path.join(DOCS_DATA, "collections.yml"), "w") as file:
        yaml.dump(stream=file, data=sanitize_mapping(read_collections()))


if __name__ == "__main__":
    export_yaml()
