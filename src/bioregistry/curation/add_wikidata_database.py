"""Add Wikidata databases."""

import click
import wikidata_client

from bioregistry import manager

#: A query over parts of (P361) the OBO Foundry (Q4117183)
#: that gets the short names (P1813), which are OBO Foundry prefixes
SPARQL = """\
SELECT ?prefix ?item ?itemLabel
WHERE
{
  ?item wdt:P361 wd:Q4117183 .
  OPTIONAL { ?item wdt:P1813 ?prefix . }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "[AUTO_LANGUAGE],mul,en". }
}
"""


@click.command()
def main() -> None:
    """Add missing wikidata entity mappings."""
    for resource in manager.registry.values():
        w = resource.get_wikidata_entity()
        if not w:
            continue
        if not resource.mappings:
            resource.mappings = {}
        if "wikidata.entity" not in resource.mappings:
            resource.mappings["wikidata.entity"] = w

    obo_to_bioregistry = manager.get_registry_invmap("obofoundry", normalize=True)
    for record in wikidata_client.query(SPARQL):
        obo_prefix = record["prefix"].casefold()
        bioregistry_prefix = obo_to_bioregistry.get(obo_prefix)
        if bioregistry_prefix:
            resource = manager.registry[bioregistry_prefix]
            if not resource.mappings:
                resource.mappings = {}

            resource.mappings["wikidata.entity"] = record["item"]

    manager.write_registry()


if __name__ == "__main__":
    main()
