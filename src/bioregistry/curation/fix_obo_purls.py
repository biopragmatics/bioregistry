"""Fix OBO PURLs as default URI prefixes."""

import click

from bioregistry import manager

__all__ = [
    "main",
]


@click.command(name="standardize-obo-uris")
def main():
    """Fix OBO PURLs as default URI prefixes."""
    for resource in manager.registry.values():
        if resource.is_deprecated():
            continue
        if not resource.get_obofoundry_prefix():
            continue
        resource.uri_format = resource.get_rdf_uri_format()
    manager.write_registry()


if __name__ == "__main__":
    main()
