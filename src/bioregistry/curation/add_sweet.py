"""Add SWEET ontologies."""

from typing import cast

import click
import pystow

import bioregistry

MODULE = pystow.module("bioregistry", "sweet")

ALL_PREFIXES_URL = "https://github.com/ESIPFed/sweet/raw/refs/heads/master/sweetPrefixes.ttl"


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
        else:
            click.echo(f"[{sweet_internal_prefix}] missing example")
            continue

        if not sweet_internal_prefix.startswith("so"):
            raise ValueError

        prefix = f"sweet.{sweet_internal_prefix.removeprefix('so')}"
        resource = bioregistry.Resource(
            prefix=prefix,
            synonyms=[sweet_internal_prefix],
            name=name,
            homepage=str(uri_prefix),
            uri_format=f"{uri_prefix}$1",
            description="The Semantic Web for Earth and Environmental Terminology (SWEET) ontology for "
            + name.removeprefix("SWEET Ontology "),
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
