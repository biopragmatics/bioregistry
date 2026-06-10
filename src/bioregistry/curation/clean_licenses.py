"""Standardize licenses."""

import click
from tqdm import tqdm

import bioregistry
from bioregistry import manager
from bioregistry.license_standardizer import standardize_license

__all__ = [
    "main",
]


@click.command(name="standardize-licenses")
def main() -> None:
    """Standardize manually curated licenses."""
    for resource in tqdm(
        bioregistry.manager.registry.values(),
        unit="resource",
        desc="Standardizing manually curated licenses",
    ):
        if resource.license:
            resource.license = standardize_license(resource.license, passthrough=True)
        elif license_str := resource.get_license():
            resource.license = standardize_license(license_str, passthrough=False)
    manager.write_registry()


if __name__ == "__main__":
    main()
