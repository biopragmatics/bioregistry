"""This script suggests prefixes that might be providers for uniprot."""

import click
from tabulate import tabulate

import bioregistry

FALSE_POSITIVES = {
    "panther.pathway",
    "panther.pthcmp",
    "protclustdb",
}


@click.command()
def _main():
    rows = []
    for prefix, resource in bioregistry.read_registry().items():
        if prefix == "uniprot" or prefix in FALSE_POSITIVES:
            continue
        example = resource.get_example()
        if example is None:
            continue
        if resource.provides:
            continue
        if bioregistry.is_known_identifier("uniprot", example):
            rows.append((prefix, example, bioregistry.get_uri_format(prefix)))
    click.echo(tabulate(rows, headers=["prefix", "example", "uri_format"]))


if __name__ == "__main__":
    _main()
