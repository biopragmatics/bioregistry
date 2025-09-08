"""Standardize licenses."""

import click
from tqdm import tqdm

from bioregistry import manager
from bioregistry.license_standardizer import standardize_license

__all__ = [
    "main",
]


@click.command(name="standardize-licenses")
def main() -> None:
    """Standardize manually curated licenses."""
    licensed = [resource for resource in manager.registry.values() if resource.license]
    for resource in tqdm(licensed, unit="resource", desc="Standardizing manually curated licenses"):
        resource.license = standardize_license(resource.license)
    manager.write_registry()


if __name__ == "__main__":
    main()
