"""Add providers for Crop Ontology entries."""

import click
import requests

import bioregistry
from bioregistry import Resource
from bioregistry.curation.utils import resource_mutator


@resource_mutator()
def main(resource: Resource) -> None:
    """Run the script."""
    prefix = resource.prefix
    if not prefix.startswith("co_"):
        return
    if not resource.repository:
        resource.repository = "https://github.com/bioversity/Crop-Ontology"
    if not resource.preferred_prefix:
        resource.preferred_prefix = prefix.upper()
    if not resource.get_license():
        resource.license = "CC BY 4.0"
    if not resource.example:
        click.echo(f"{prefix} missing example")
        return
    if resource.uri_format:
        click.echo(f"{prefix} has url {resource.uri_format}")
        url = bioregistry.get_iri(prefix, resource.example)
        if url is None:
            raise RuntimeError
        res = requests.get(url, timeout=15)
        click.echo(res.text)
        click.echo("")
        return
    resource.uri_format = f"https://cropontology.org/rdf/{prefix.upper()}:$1"


if __name__ == "__main__":
    main()
