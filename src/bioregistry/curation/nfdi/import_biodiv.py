"""Import the NFDI4Biodiversity collection from https://biodivportal.gfbio.org."""

import click
from tabulate import tabulate

import bioregistry
from bioregistry.external.bioportal import get_biodivportal
from bioregistry.external.bioportal.bioportal import AgroPortalAligner, BioDivPortalAligner

COLLECTION_IDENTIFIER = "0000040"


@click.command()
@click.option("--add", is_flag=True)
def import_biodiv(add: bool) -> None:
    """Import biodiversity."""
    BioDivPortalAligner.align(force_download=False)
    AgroPortalAligner.align(force_download=False)  # meaningful overlap
    records = get_biodivportal(force_download=False)
    biodivportal_to_internal = bioregistry.get_registry_invmap("biodivportal")
    rows = []
    for acronym, record in records.items():
        if acronym in biodivportal_to_internal:
            bioregistry.add_to_collection(COLLECTION_IDENTIFIER, biodivportal_to_internal[acronym])
        elif norm_id := bioregistry.normalize_prefix(acronym):
            bioregistry.add_to_collection(COLLECTION_IDENTIFIER, norm_id)
        else:
            if add:
                prefix_part = acronym.lower().replace("_", "").replace("-", "")
                bioregistry.add_resource(
                    bioregistry.Resource(
                        prefix=f"gfbio.{prefix_part}",
                        mappings={"biodivportal": acronym},
                    )
                )
            rows.append(
                (
                    acronym,
                    record["name"],
                    f"https://biodivportal.gfbio.org/ontologies/{acronym}",
                    record.get("extras", {}).get("example_uri"),
                )
            )
    click.echo(
        tabulate(
            rows,
            headers=["prefix", "name", "homepage", "example"],
            showindex=True,
            tablefmt="github",
        )
    )
    bioregistry.manager.write_collections()
    if add:
        BioDivPortalAligner.align(force_download=False)
        bioregistry.manager.write_registry()


if __name__ == "__main__":
    import_biodiv()
