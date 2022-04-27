"""Remove uninformative suffixes in names of resources."""

import click
from tabulate import tabulate

import bioregistry

suffixes = ["id", "accession"]


@click.command()
def _main():
    rows = []
    registry = bioregistry.read_registry()
    for prefix, resource in registry.items():
        name = bioregistry.get_name(prefix)
        for suffix in suffixes:
            if name.lower().endswith(f" {suffix}"):
                resource.name = name[: -len(suffix) - 1]
                rows.append((prefix, name))
    click.echo(tabulate(rows, headers=["prefix", "name"], tablefmt="github"))
    bioregistry.write_registry(registry)


if __name__ == "__main__":
    _main()
