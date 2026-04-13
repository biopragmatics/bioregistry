"""Import the NFDI4Biodiversity collection from https://biodivportal.gfbio.org."""

import click
from tabulate import tabulate

import bioregistry
from bioregistry.external.bioportal import get_biodivportal

COLLECTION_IDENTIFIER = "0000040"


@click.command()
def import_biodiv() -> None:
    """Import biodiversity."""
    records = get_biodivportal()

    rows = []
    for acronym, record in records.items():
        if norm_id := bioregistry.normalize_prefix(acronym):
            bioregistry.add_to_collection(COLLECTION_IDENTIFIER, norm_id)
        else:
            rows.append(
                (acronym, record["name"], f"https://biodivportal.gfbio.org/ontologies/{acronym}")
            )
    click.echo(tabulate(rows, headers=["prefix", "name", "homepae"]))
    bioregistry.manager.write_collections()


if __name__ == "__main__":
    import_biodiv()
