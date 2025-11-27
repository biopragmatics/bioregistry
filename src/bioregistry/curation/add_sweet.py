"""Add SWEET ontologies."""

import pystow

import bioregistry

MODULE = pystow.module("bioregistry", "sweet")

ALL_PREFIXES_URL = "https://github.com/ESIPFed/sweet/raw/refs/heads/master/sweetPrefixes.ttl"


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
    for prefix, namespace in graph.query(sparql):  # type:ignore
        if prefix == "soall":
            continue  # this is the combine one, not its own prefix

        key = namespace.removeprefix("http://sweetontology.net/").rstrip("/")
        if not key:
            continue

        url = f"https://github.com/ESIPFed/sweet/raw/refs/heads/master/src/{key}.ttl"
        inner_graph = MODULE.ensure_rdf(url=url)

        ontology_name_query = """
            SELECT ?name
            WHERE { owl:Ontology ^rdf:type/rdfs:label ?name }
            LIMIT 1
        """
        res = inner_graph.query(ontology_name_query)
        name = str(next(iter(res))[0])  # type:ignore

        example_query = f"""
            SELECT ?term ?name
            WHERE {{
                ?term rdf:type owl:Class;
                      rdfs:label ?name ;

                FILTER STRSTARTS(str(?term), "{namespace}")
            }}
            LIMIT 1
        """
        example_records = list(inner_graph.query(example_query))
        if example_records:
            example_uri, _example_name = example_records[0]  # type:ignore
            example = example_uri.removeprefix(namespace)
        else:
            example = None

        if not prefix.startswith("so"):
            raise ValueError
        resource = bioregistry.Resource(
            prefix=f"sweet.{prefix.removeprefix('so')}",
            synonyms=[prefix, f"sweet.{key.lower()}"],
            name=name,
            homepage=str(namespace),
            uri_format=f"{namespace}$1",
            description="The Semantic Web for Earth and Environmental Terminology (SWEET) ontology for "
            + name.removeprefix("SWEET Ontology "),
            example=example,
            download_rdf=url,
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
