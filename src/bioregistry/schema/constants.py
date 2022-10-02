# -*- coding: utf-8 -*-

"""Schema constants."""

from dataclasses import dataclass
from typing import Mapping, Optional, Union

import rdflib.namespace
from rdflib import DCTERMS, FOAF, RDF, RDFS, SKOS, XSD, Literal, URIRef
from rdflib.term import Node

__all__ = [
    "bioregistry_schema_terms",
    # Namespaces
    "bioregistry_collection",
    "bioregistry_resource",
    "bioregistry_metaresource",
    "bioregistry_schema",
    "orcid",
]


@dataclass
class Term:
    """A tuple for a term."""

    identifier: str
    type: str
    label: str
    description: str


@dataclass
class ClassTerm(Term):
    """A term for a class."""

    xref: Optional[URIRef] = None


@dataclass
class PropertyTerm(Term):
    """A term for a property."""

    domain: Union[str, Node]
    range: Union[str, Node]


bioregistry_schema_terms = [
    ClassTerm("0000001", "Class", "Resource", "A type for entries in the Bioregistry's registry."),
    ClassTerm(
        "0000002", "Class", "Registry", "A type for entries in the Bioregistry's metaregistry."
    ),
    ClassTerm(
        "0000003", "Class", "Collection", "A type for entries in the Bioregistry's collections"
    ),
    # ClassTerm(
    #     "0000004",
    #     "Class",
    #     "Mapping",
    #     "A type, typically instantiated as a blank node, that connects a given resource to a metaresource"
    #     " and a metaidentifier using the hasMetaresource and hasMetaidentifier relations.",
    # ),
    PropertyTerm(
        "0000005",
        "Property",
        "has example",
        "An identifier for a resource or metaresource.",
        domain="0000001",
        range=XSD.string,
    ),
    PropertyTerm(
        "0000006",
        "Property",
        "has provider formatter",
        "The URL format for a provider that contains $1 for the identifier (or metaidentifier)"
        " that should be resolved.",
        domain="0000001",
        range=XSD.string,
    ),
    PropertyTerm(
        "0000007",
        "Property",
        "has resolver formatter",
        "The URL format for a resolver that contains $1 for the prefix and $2 for the identifier"
        " that should be resolved.",
        domain="0000002",
        range=XSD.string,
    ),
    PropertyTerm(
        "0000008",
        "Property",
        "has pattern",
        "The pattern for identifiers in the given resource",
        domain="0000001",
        range=XSD.string,
    ),
    # PropertyTerm(
    #     "0000009",
    #     "Property",
    #     "has contact email",
    #     "The email of the contact person for the given resource",
    #     domain="0000001",
    #     range=XSD.string,
    # ),
    PropertyTerm(
        "0000010",
        "Property",
        "has download URL",
        "A download link for the given resource",
        domain="0000001",
        range=XSD.string,
    ),
    PropertyTerm(
        "0000011",
        "Property",
        "provides for",
        "For resources that do not create their own controlled vocabulary, this relation should be used"
        " to point to a different resource that it uses. For example, CTD's gene resource provides for"
        " the NCBI Entrez Gene resource.",
        domain="0000001",
        range="0000001",
    ),
    PropertyTerm(
        "0000012",
        "Property",
        "is deprecated",
        "A property whose subject is a resource that denotes if it is still available and usable?"
        " Currently this is a blanket term for decommissioned, unable to locate, abandoned, etc.",
        domain="0000001",
        range=XSD.boolean,
    ),
    # PropertyTerm(
    #     "0000013",
    #     "Property",
    #     "has mapping",
    #     "A property whose subject is a resource and object is a mapping",
    #     domain="0000001",
    #     range="0000004",
    # ),
    # PropertyTerm(
    #     "0000014",
    #     "Property",
    #     "has registry",
    #     "A property whose subject is a mapping and object is a metaresource.",
    #     domain="0000004",
    #     range="0000002",
    # ),
    # PropertyTerm(
    #     "0000015",
    #     "Property",
    #     "has metaidentifier",
    #     "A property whose subject is a mapping and object is an identifier string.",
    #     domain="0000004",
    #     range=XSD.string,
    # ),
    PropertyTerm(
        "0000016",
        "Property",
        "has canonical",
        "A property connecting two prefixes that share an IRI where the subject is "
        "the non-preferred prefix and the target is the preferred prefix",
        domain="0000001",
        range="0000001",
    ),
    PropertyTerm(
        "0000017",
        "Property",
        "depends on",
        "The data in resource denoted by the subject prefix depends on the data "
        "in the resources denoted by the object prefix",
        domain="0000001",
        range="0000001",
    ),
    PropertyTerm(
        "0000018",
        "Property",
        "appears in",
        "Terms from the source appear in the target resource",
        domain="0000001",
        range="0000001",
    ),
    PropertyTerm(
        "0000019",
        "Property",
        "has responsible",
        "The responsible person for a resource",
        domain="0000001",
        range="0000020",
    ),
    ClassTerm(
        "0000020",
        "Class",
        "Person",
        "A person",
        xref=FOAF.Person,
    ),
    PropertyTerm(
        "0000021",
        "Property",
        "has reviewer",
        "The reviewer of a prefix",
        domain="0000001",
        range="0000020",
    ),
    PropertyTerm(
        "0000022",
        "Property",
        "has responsible",
        "The main contact person for a registry",
        domain="0000002",
        range="0000020",
    ),
]
bioregistry_schema_extras = [
    ("0000001", DCTERMS.isPartOf, "part of", "0000002"),  # resource part of registry
    ("0000001", DCTERMS.isPartOf, "part of", "0000003"),  # resource part of collection
    ("0000003", DCTERMS.contributor, "contributor", "0000020"),  # author creator of collection
    ("0000001", DCTERMS.contributor, "contributor", "0000020"),  # author creator of resource
    ("0000001", SKOS.exactMatch, "exact match", "0000001"),  # resource equivalence
]
bioregistry_collection = rdflib.namespace.Namespace("https://bioregistry.io/collection/")
bioregistry_resource = rdflib.namespace.Namespace("https://bioregistry.io/registry/")
bioregistry_metaresource = rdflib.namespace.Namespace("https://bioregistry.io/metaregistry/")
bioregistry_schema = rdflib.namespace.ClosedNamespace(
    uri=URIRef("https://bioregistry.io/schema/#"),
    terms=[term.identifier for term in bioregistry_schema_terms],
)
bioregistry_class_to_id: Mapping[str, URIRef] = {
    term.label: bioregistry_schema[term.identifier]
    for term in bioregistry_schema_terms
    if term.type == "Class"
}
orcid = rdflib.namespace.Namespace("https://orcid.org/")


def get_schema_rdf() -> rdflib.Graph:
    """Get the Bioregistry schema as an RDF graph."""
    graph = rdflib.Graph()
    graph.bind("bioregistry.schema", bioregistry_schema)
    graph.bind("bioregistry.collection", bioregistry_collection)
    graph.bind("bioregistry", bioregistry_resource)
    graph.bind("dcterms", DCTERMS)
    for term in bioregistry_schema_terms:
        node = bioregistry_schema[term.identifier]
        if isinstance(term, ClassTerm):
            graph.add((node, RDF.type, RDFS.Class))
        elif isinstance(term, PropertyTerm):
            graph.add((node, RDF.type, RDF.Property))
            for property_node, object_node in (
                (RDFS.domain, term.domain),
                (RDFS.range, term.range),
            ):
                if isinstance(object_node, Node):
                    graph.add((node, property_node, object_node))
                elif isinstance(object_node, str):
                    graph.add((node, property_node, bioregistry_schema[object_node]))
                else:
                    raise TypeError(term)
        else:
            raise TypeError(term)
        graph.add((node, RDFS.label, Literal(term.label)))
        graph.add((node, DCTERMS.description, Literal(term.description)))
    return graph


def get_schema_nx():
    """Get the schema as a networkx multidigraph."""
    import networkx as nx

    graph = nx.MultiDiGraph()
    for term in bioregistry_schema_terms:
        if isinstance(term, ClassTerm):
            graph.add_node(term.identifier, label=term.label)

    for term in bioregistry_schema_terms:
        if not isinstance(term, PropertyTerm):
            continue
        range = None if isinstance(term.range, URIRef) else term.range
        domain = None if isinstance(term.domain, URIRef) else term.domain
        if range and domain:
            graph.add_edge(domain, range, label=term.label)

    for s, _p, p_label, o in bioregistry_schema_extras:
        graph.add_edge(s, o, label=p_label)

    for node in list(graph):
        if node not in graph[node]:
            continue
        labels = {data["label"] for data in graph[node][node].values()}
        graph.remove_edges_from([(node, node, k) for k in graph[node][node]])
        graph.add_edge(node, node, label=",\n".join(labels))

    return graph
