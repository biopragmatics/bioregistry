"""Summarize NFDI consortia that don't have a collection."""

import click
import wikidata_client

import bioregistry
from bioregistry import Author, Collection, Organization

SPARQL = """\
SELECT ?wikidata ?name ?ror
WHERE {
    ?wikidata wdt:P361 wd:Q61658497; wdt:P31 wd:Q98270496 ; rdfs:label ?name .
    FILTER (LANG(?name) = 'en')
    OPTIONAL { ?wikidata wdt:P6782 ?ror . }
}
"""


@click.command()
def main() -> None:
    """Summarize NFDI consortia that don't have a collection."""
    collections = bioregistry.read_collections()
    max_collection_id = max(map(int, collections))

    wikidata_client.query(SPARQL)

    nfdi_organizations = [
        Organization.model_validate(record) for record in wikidata_client.query(SPARQL)
    ]
    wikidata_to_organization: dict[str, Organization] = {
        organization.wikidata: organization
        for organization in nfdi_organizations
        if organization.wikidata
    }
    covered_wikidata: set[str] = {
        organization.wikidata
        for collection in collections.values()
        for organization in collection.organizations or []
        if organization.wikidata
    }
    missing = set(wikidata_to_organization) - covered_wikidata
    if missing:
        nfdi = Organization(name="NFDI", wikidata="Q61658497", ror="05qj6w324")
        for wikidata in sorted(missing):
            organization = wikidata_to_organization[wikidata]
            max_collection_id += 1
            collection = Collection(
                identifier=f"{max_collection_id:07}",
                name=f"{organization.name} Collection",
                description=f"A collection of ontologies, controlled vocabularies, database, and schemas relevant for {organization.name}",
                resources=["bioregistry"],
                authors=[Author.get_charlie()],
                organizations=[organization, nfdi],
            )
            bioregistry.manager.add_collection(collection)
        bioregistry.manager.write_collections()


if __name__ == "__main__":
    main()
