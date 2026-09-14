"""Export components of the bioregistry to YAML."""

from __future__ import annotations

from typing import TYPE_CHECKING

import click

if TYPE_CHECKING:
    from ..resource_manager import Manager

__all__ = ["export_yaml", "export_yaml_helper"]


@click.command()
def export_yaml() -> None:
    """Export the registry as YAML."""
    export_yaml_helper()


def export_yaml_helper(manager_: Manager | None = None, output: bool = True) -> None:
    """Help export the bioregistry to YAML."""
    from pystow.utils import write_json, write_yaml

    from ..constants import (
        COLLECTIONS_YAML_PATH,
        METAREGISTRY_YAML_PATH,
        REGISTRY_JSON_PATH,
        REGISTRY_YAML_PATH,
    )
    from ..resource_manager import Manager
    from ..schema import sanitize_mapping
    from ..utils import get_hexdigests, registry_yaml_dumper

    registry_yaml_dumper()

    pre_digests = get_hexdigests()

    if manager_ is None:
        manager_ = Manager()

    registry = manager_.rasterize()
    metaregistry = sanitize_mapping(manager_.metaregistry)
    collections = sanitize_mapping(manager_.collections)

    write_yaml(registry, REGISTRY_YAML_PATH)
    write_json(registry, REGISTRY_JSON_PATH, indent=2, sort_keys=True)
    write_yaml(metaregistry, METAREGISTRY_YAML_PATH)
    write_yaml(collections, COLLECTIONS_YAML_PATH)

    if pre_digests != get_hexdigests() and output:
        click.echo("::set-output name=BR_UPDATED::true")


if __name__ == "__main__":
    export_yaml()
