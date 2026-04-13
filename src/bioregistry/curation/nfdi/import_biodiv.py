from ontoportal_client import BioDivPortal
import click
from pathlib import Path
import json
from tabulate import tabulate

import bioregistry

COLLECTION_IDENTIFIER = "0000040"


@click.command()
def import_biodiv() -> None:
    """Import biodiversity."""
    path = Path(__file__).parent.joinpath("data.json")
    if not path.is_file():
        client = BioDivPortal()
        ontologies = client.get_ontologies()
        path.write_text(json.dumps(ontologies, indent=2))
    else:
        ontologies = json.loads(path.read_text())

    rows = []
    for ontology in ontologies:
        name = ontology["name"]
        acronym = ontology["acronym"]
        if norm_id := bioregistry.normalize_prefix(acronym):
            bioregistry.add_to_collection(COLLECTION_IDENTIFIER, norm_id)
        else:
            rows.append((acronym, name, f"https://biodivportal.gfbio.org/ontologies/{acronym}"))
    click.echo(tabulate(rows, headers="keys"))
    bioregistry.manager.write_collections()


if __name__ == '__main__':
    import_biodiv()
