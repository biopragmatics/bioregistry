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
from ..resource_manager import Manager
from ..schema import sanitize_mapping
from ..utils import get_hexdigests

__all__ = ["export_yaml", "export_yaml_helper"]


@click.command()
def export_yaml() -> None:
    """Export the registry as YAML."""
    export_yaml_helper()


def export_yaml_helper(manager_: Manager | None = None, output: bool = True) -> None:
    """Help export the bioregistry to YAML."""
    pre_digests = get_hexdigests()

    if manager_ is None:
        manager_ = Manager()

    registry = manager_.rasterize()
    metaregistry = sanitize_mapping(manager_.metaregistry)
    collections = sanitize_mapping(manager_.collections)

    with REGISTRY_YAML_PATH.open("w") as file:
        yaml.safe_dump(stream=file, data=registry, allow_unicode=True)
    with REGISTRY_JSON_PATH.open("w") as file:
        json.dump(registry, file, indent=2, sort_keys=True, ensure_ascii=False)

    with METAREGISTRY_YAML_PATH.open("w") as file:
        yaml.safe_dump(stream=file, data=metaregistry, allow_unicode=True)
    with COLLECTIONS_YAML_PATH.open("w") as file:
        yaml.safe_dump(stream=file, data=collections, allow_unicode=True)

    if pre_digests != get_hexdigests() and output:
        click.echo("::set-output name=BR_UPDATED::true")


if __name__ == "__main__":
    export_yaml()
