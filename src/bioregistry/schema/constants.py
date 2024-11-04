# -*- coding: utf-8 -*-

"""Schema constants."""

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, List, Mapping, Optional, Union

import rdflib.namespace
from rdflib import (
    DCAT,
    DCTERMS,
    DOAP,
    FOAF,
    OWL,
    RDF,
    RDFS,
    SH,
    SKOS,
    VANN,
    VOID,
    XSD,
    Literal,
    URIRef,
)
from rdflib.term import Node

if TYPE_CHECKING:
    import networkx

    import bioregistry.resource_manager

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

    xrefs: List[URIRef] = field(default_factory=list)


@dataclass
class PropertyTerm(Term):
    """A term for a property."""

    domain: Union[str, Node]
    range: Union[str, Node]
    xrefs: List[URIRef] = field(default_factory=list)
    parent: Optional[URIRef] = None


IDOT = rdflib.Namespace("http://identifiers.org/idot/")
ROR = rdflib.Namespace("https://ror.org/")
WIKIDATA = rdflib.Namespace("http://www.wikidata.org/entity/")
OBOINOWL = rdflib.Namespace("http://www.geneontology.org/formats/oboInOwl#")
BRIDGEDB = rdflib.Namespace("http://vocabularies.bridgedb.org/ops#")

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
        "has local unique identifier example",
        "An identifier for a resource or metaresource.",
        domain="0000001",
        range=XSD.string,
        xrefs=[IDOT["exampleIdentifier"], VANN["example"], BRIDGEDB["idExample"]],
    ),
    PropertyTerm(
        "0000006",
        "Property",
        "has provider formatter",
        "The URL format for a provider that contains $1 for the identifier (or metaidentifier)"
        " that should be resolved.",
        domain="0000001",
        range=XSD.string,
        xrefs=[
            IDOT["accessPattern"],
            WIKIDATA["P1630"],
            BRIDGEDB["hasPrimaryUriPattern"],
        ],
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
        "has local unique identifier pattern",
        "The pattern for identifiers in the given resource",
        domain="0000001",
        range=XSD.string,
        xrefs=[
            IDOT["identifierPattern"],
            WIKIDATA["P1793"],
            BRIDGEDB["hasRegexPattern"],
        ],
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
        "the non-preferred prefix and the target is the preferred prefix. "
        "See examples [here](https://bioregistry.io/highlights/relations#canonical).",
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
        xrefs=[FOAF.Person],
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
    PropertyTerm(
        "0000023",
        "Property",
        "has alternative prefix",
        "An alternative or synonymous prefix",
        domain="0000001",
        range=XSD.string,
        xrefs=[IDOT["alternatePrefix"]],
        parent=OBOINOWL["hasExactSynonym"],
    ),
    PropertyTerm(
        "0000024",
        "Property",
        "has URI prefix",
        "The URL prefix for a provider that does not $1 for the identifier (or metaidentifier)"
        " that should be resolved.",
        domain="0000001",
        range=XSD.string,
        xrefs=[VANN.preferredNamespaceUri, VOID.uriSpace, SH.namespace],
    ),
    ClassTerm(
        "0000025",
        "Class",
        "Organization",
        "An organization",
    ),
    PropertyTerm(
        "0000026",
        "Property",
        "has identifier space owner",
        "An organization",
        domain="0000001",
        range="0000025",
    ),
    PropertyTerm(
        "0000027",
        "Property",
        "has resource example",
        "An expanded example URL for a resource or metaresource.",
        domain="0000001",
        range=XSD.string,
        xrefs=[
            VOID.exampleResource,
        ],
    ),
    PropertyTerm(
        "0000028",
        "Property",
        "has URI pattern",
        "The pattern for expanded URIs in the given resource",
        domain="0000001",
        range=XSD.string,
        xrefs=[
            VOID.uriRegexPattern,
            WIKIDATA["P8966"],
            IDOT["accessIdentifierPattern"],
        ],
    ),
    PropertyTerm(
        "0000029",
        "Property",
        "has prefix",
        "has canonical prefix",
        domain="0000001",
        range=XSD.string,
        xrefs=[
            SH.prefix,
            VANN.preferredNamespacePrefix,
            IDOT["preferredPrefix"],
            BRIDGEDB["systemCode"],
        ],
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


def _graph(manager: Optional["bioregistry.resource_manager.Manager"] = None) -> rdflib.Graph:
    graph = rdflib.Graph()
    graph.namespace_manager.bind("bioregistry", bioregistry_resource)
    graph.namespace_manager.bind("bioregistry.metaresource", bioregistry_metaresource)
    graph.namespace_manager.bind("bioregistry.collection", bioregistry_collection)
    graph.namespace_manager.bind("bioregistry.schema", bioregistry_schema)
    graph.namespace_manager.bind("orcid", orcid)
    graph.namespace_manager.bind("foaf", FOAF)
    graph.namespace_manager.bind("dcat", DCAT)
    graph.namespace_manager.bind("dcterms", DCTERMS)
    graph.namespace_manager.bind("skos", SKOS)
    graph.namespace_manager.bind("obo", rdflib.Namespace("http://purl.obolibrary.org/obo/"))
    graph.namespace_manager.bind("idot", IDOT)
    graph.namespace_manager.bind("wikidata", WIKIDATA)
    graph.namespace_manager.bind("vann", VANN)
    graph.namespace_manager.bind("ror", ROR)
    graph.namespace_manager.bind("oboinowl", OBOINOWL)
    graph.namespace_manager.bind("void", VOID)
    graph.namespace_manager.bind("doap", DOAP)
    graph.namespace_manager.bind("sh", SH)
    if manager:
        for key, value in manager.get_internal_prefix_map().items():
            graph.namespace_manager.bind(key, value)
    return graph


def get_schema_rdf() -> rdflib.Graph:
    """Get the Bioregistry schema as an RDF graph."""
    graph = _graph()
    _add_schema(graph)
    return graph


def _add_schema(graph: rdflib.Graph) -> rdflib.Graph:
    for term in bioregistry_schema_terms:
        node = bioregistry_schema[term.identifier]
        if isinstance(term, ClassTerm):
            graph.add((node, RDF.type, RDFS.Class))
            for xref in term.xrefs:
                graph.add((node, OWL.equivalentClass, xref))
        elif isinstance(term, PropertyTerm):
            graph.add((node, RDF.type, RDF.Property))
            for xref in term.xrefs:
                graph.add((node, OWL.equivalentProperty, xref))
            if term.parent is not None:
                graph.add((node, RDFS.subPropertyOf, term.parent))
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


def get_schema_nx() -> "networkx.MultiDiGraph":
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
