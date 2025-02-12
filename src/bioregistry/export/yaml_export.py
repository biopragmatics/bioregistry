"""Export components of the bioregistry to YAML."""

import json

import click
import yaml

from ..constants import (
    COLLECTIONS_YAML_PATH,
    METAREGISTRY_YAML_PATH,
    REGISTRY_JSON_PATH,
    REGISTRY_YAML_PATH,
)
from ..resource_manager import manager
from ..schema import sanitize_mapping
from ..schema_utils import read_collections, read_metaregistry
from ..utils import get_hexdigests


@click.command()
def export_yaml():
    """Export the registry as YAML."""
    pre_digests = get_hexdigests()

    registry = manager.rasterize()
    metaregistry = sanitize_mapping(read_metaregistry())
    collections = sanitize_mapping(read_collections())

    with REGISTRY_YAML_PATH.open("w") as file:
        yaml.safe_dump(stream=file, data=registry, allow_unicode=True)
    with REGISTRY_JSON_PATH.open("w") as file:
        json.dump(registry, file, indent=2, sort_keys=True, ensure_ascii=False)

    with METAREGISTRY_YAML_PATH.open("w") as file:
        yaml.safe_dump(stream=file, data=metaregistry, allow_unicode=True)
    with COLLECTIONS_YAML_PATH.open("w") as file:
        yaml.safe_dump(stream=file, data=collections, allow_unicode=True)

    if pre_digests != get_hexdigests():
        click.echo("::set-output name=BR_UPDATED::true")


if __name__ == "__main__":
    export_yaml()
