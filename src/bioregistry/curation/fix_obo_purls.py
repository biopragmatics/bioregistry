"""Fix OBO PURLs as default URI prefixes."""

import click
from tqdm import tqdm

from bioregistry import manager
from bioregistry.license_standardizer import standardize_license

__all__ = [
    "main",
]


@click.command(name="standardize-obo-uris")
def main():
    """Standardize OBO Foundry URIs."""
    for resource in manager.registry.values():
        if resource.is_deprecated():
            continue
        if not resource.get_obofoundry_prefix():
            continue
        resource.uri_format = resource.get_rdf_uri_format()
    manager.write_registry()


if __name__ == "__main__":
    main()
