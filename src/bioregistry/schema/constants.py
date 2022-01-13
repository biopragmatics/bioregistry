# -*- coding: utf-8 -*-

"""Schema constants."""

from collections import namedtuple
from typing import Mapping

import rdflib.namespace
from rdflib import URIRef

__all__ = [
    "bioregistry_schema_terms",
    # Namespaces
    "bioregistry_collection",
    "bioregistry_resource",
    "bioregistry_metaresource",
    "bioregistry_schema",
    "orcid",
]

Term = namedtuple("Term", "identifier type label description")

bioregistry_schema_terms = [
    Term("0000001", "Class", "Resource", "A type for entries in the Bioregistry's registry."),
    Term("0000002", "Class", "Registry", "A type for entries in the Bioregistry's metaregistry."),
    Term("0000003", "Class", "Collection", "A type for entries in the Bioregistry's collections"),
    Term(
        "0000004",
        "Class",
        "Mapping",
        "A type, typically instantiated as a blank node, that connects a given resource to a metaresource"
        " and a metaidentifier using the hasMetaresource and hasMetaidentifier relations.",
    ),
    Term("0000005", "Property", "hasExample", "An identifier for a resource or metaresource."),
    Term(
        "0000006",
        "Property",
        "hasProviderFormatter",
        "The URL format for a provider that contains $1 for the identifier (or metaidentifier)"
        " that should be resolved.",
    ),
    Term(
        "0000007",
        "Property",
        "hasResolverFormatter",
        "The URL format for a resolver that contains $1 for the prefix and $2 for the identifier"
        " that should be resolved.",
    ),
    Term("0000008", "Property", "hasPattern", "The pattern for identifiers in the given resource"),
    Term(
        "0000009",
        "Property",
        "hasContactEmail",
        "The email of the contact person for the given resource",
    ),
    Term("0000010", "Property", "hasDownloadURL", "A download link for the given resource"),
    Term(
        "0000011",
        "Property",
        "providesFor",
        "For resources that do not create their own controlled vocabulary, this relation should be used"
        " to point to a different resource that it uses. For example, CTD's gene resource provides for"
        " the NCBI Entrez Gene resource.",
    ),
    Term(
        "0000012",
        "Property",
        "isDeprecated",
        "A property whose subject is a resource that denotes if it is still available and usable?"
        " Currently this is a blanket term for decommissioned, unable to locate, abandoned, etc.",
    ),
    Term(
        "0000013",
        "Property",
        "hasMapping",
        "A property whose subject is a resource and object is a mapping",
    ),
    Term(
        "0000014",
        "Property",
        "hasRegistry",
        "A property whose subject is a mapping and object is a metaresource.",
    ),
    Term(
        "0000015",
        "Property",
        "hasMetaidentifier",
        "A property whose subject is a mapping and object is an identifier string.",
    ),
    Term(
        "0000016",
        "Property",
        "hasCanonical",
        "A property connecting two prefixes that share an IRI where the subject is "
        "the non-preferred prefix and the target is the preferred prefix",
    ),
    Term(
        "0000017",
        "Property",
        "dependsOn",
        "The data in resource denoted by the subject prefix depends on the data "
        "in the resources denoted by the object prefix",
    ),
    Term(
        "0000018",
        "Property",
        "appearsIn",
        "Terms from the source appear in the target resource",
    ),
    Term(
        "0000019",
        "Property",
        "hasResponsible",
        "Connect an entity to its responsible person",
    ),
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
