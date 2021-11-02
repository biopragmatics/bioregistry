# -*- coding: utf-8 -*-

"""Add providers for Crop Ontology entries."""

import click
import requests

import bioregistry


@click.command()
def main():
    """Run the script."""
    r = dict(bioregistry.read_registry())
    for prefix, resource in r.items():
        if not prefix.startswith("co_"):
            continue
        if not resource.example:
            click.echo(f"{prefix} missing example")
            continue
        if resource.uri_format:
            click.echo(f"{prefix} has url {resource.uri_format}")
            url = bioregistry.get_iri(prefix, resource.example)
            res = requests.get(url)
            click.echo(res.text)
            click.echo("")
            continue
        resource.uri_format = f"https://www.cropontology.org/rdf/{prefix.upper()}:$1"
    bioregistry.write_registry(r)


if __name__ == "__main__":
    main()
