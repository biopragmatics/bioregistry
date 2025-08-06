"""Add Wikidata databases."""

#: A query over parts of (P361) the OBO Foundry (Q4117183)
#: that gets the short names, which are OBO Foundry prefixes
SPARQL = """\
SELECT ?prefix ?item ?itemLabel
WHERE
{
  ?item wdt:P361 wd:Q4117183 .
  OPTIONAL { ?item wdt:P1813 ?prefix . }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "[AUTO_LANGUAGE],mul,en". }
}
"""

from bioregistry import manager
import click


@click.command()
def main() -> None:
    for resource in manager.registry.values():
        w = resource.get_wikidata_entity()
        if not w:
            continue
        if not resource.mappings:
            resource.mappings = {}
        if "wikidata.entity" not in resource.mappings:
            resource.mappings["wikidata.entity"] = w

    # TODO add OBO ontologies via wikidata sqarl query above

    manager.write_registry()



if __name__ == "__main__":
    main()
