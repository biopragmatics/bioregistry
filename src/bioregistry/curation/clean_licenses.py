"""Standardize licenses."""

import click
from bioregistry import manager

from bioregistry.license_standardizer import standardize_license

from tqdm import tqdm

__all__ = [
    "main",
]


@click.command(name="standardize-licenses")
def main():
    """Standardize manually curated licenses."""
    licensed = [
        resource
        for resource in manager.registry.values()
        if resource.license
    ]
    for resource in tqdm(licensed, unit="resource"):
        resource.license = standardize_license(resource.license)
    manager.write_registry()


if __name__ == "__main__":
    main()
