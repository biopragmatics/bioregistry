"""Add SWEET ontologies."""

from typing import cast

import click
import pystow

import bioregistry

MODULE = pystow.module("bioregistry", "sweet")

ALL_PREFIXES_URL = "https://github.com/ESIPFed/sweet/raw/refs/heads/master/sweetPrefixes.ttl"

MANUAL = {
    "sosto": "Acute",
    "sostri": "Catastrophic",
    "sostsp": "Big",
    "sorel": "hasPhenomena",
    "sorelch": "atomicMass",
    "sorelh": "hasAttribute",
    "soreaer": "AbyssopelagicZone",
    "sorelcl": "hasAverageAnnualPrecipitation",
}


@click.command()
def main() -> None:
    """Add SWEET ontologies."""
    graph = MODULE.ensure_rdf(url=ALL_PREFIXES_URL)
    sparql = """
        SELECT ?prefix ?namespace
        WHERE {
            ?x sh:prefix ?prefix;
               sh:namespace ?namespace .
        }
    """
    for sweet_internal_prefix, uri_prefix in graph.query(sparql):  # type:ignore
        sweet_internal_prefix = str(sweet_internal_prefix)
        uri_prefix = str(uri_prefix)

        if sweet_internal_prefix in {"soall", "sweet"}:
            continue  # this is the combine one, not its own prefix

        sweet_internal_key = uri_prefix.removeprefix("http://sweetontology.net/").rstrip("/")
        if not sweet_internal_key:
            raise ValueError(f"no internal key found for {sweet_internal_prefix}")

        download_rdf = (
            f"https://github.com/ESIPFed/sweet/raw/refs/heads/master/src/{sweet_internal_key}.ttl"
        )
        inner_graph = MODULE.ensure_rdf(url=download_rdf)

        ontology_name_query = """
            SELECT ?name
            WHERE { owl:Ontology ^rdf:type/rdfs:label ?name }
            LIMIT 1
        """
        name = str(next(iter(inner_graph.query(ontology_name_query)))[0])  # type:ignore
        name_short = name.removeprefix("SWEET Ontology ")

        example_query = f"""
            SELECT ?term
            WHERE {{
                ?term rdf:type owl:Class;
                      rdfs:label ?name ;
                FILTER STRSTARTS(str(?term), "{uri_prefix}")
            }}
            LIMIT 1
        """
        example_records = list(inner_graph.query(example_query))
        if example_records:
            example_uri = cast(str, example_records[0][0])  # type:ignore[index]
            example = example_uri.removeprefix(uri_prefix)
        elif sweet_internal_prefix in MANUAL:
            example = MANUAL[sweet_internal_prefix]
        else:
            click.echo(f"[{sweet_internal_prefix}] missing example in {name_short} ({uri_prefix})")
            continue

        if not sweet_internal_prefix.startswith("so"):
            raise ValueError

        nsl = name_short.lower()
        if nsl.startswith("human "):
            pass
        elif nsl.startswith("material "):
            pass
        elif nsl.startswith("phenomena "):
            pass
        elif nsl.startswith("property "):
            pass
        elif nsl.startswith("process "):
            pass
        elif nsl.startswith("realm land "):
            pass
        elif nsl.startswith("realm "):
            pass
        elif nsl.startswith("representation "):
            pass
        elif nsl.startswith("state "):
            pass
        else:
            click.echo(f"[{sweet_internal_prefix}] could not categorize - {name_short}")

        prefix = f"sweet.{sweet_internal_prefix.removeprefix('so')}"
        resource = bioregistry.Resource(
            prefix=prefix,
            synonyms=[sweet_internal_prefix],
            name=name,
            homepage=str(uri_prefix),
            uri_format=f"{uri_prefix}$1",
            description=f"The Semantic Web for Earth and Environmental Terminology (SWEET) ontology for {name_short}",
            example=example,
            download_rdf=download_rdf,
            part_of="sweet",
            license="CC0-1.0",
            repository="https://github.com/ESIPFed/sweet",
            contributor=bioregistry.Author.get_charlie(),
            github_request_issue=1772,
        )
        bioregistry.add_resource(resource)

    bioregistry.manager.write_registry()


if __name__ == "__main__":
    main()
