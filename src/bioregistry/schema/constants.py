# -*- coding: utf-8 -*-

"""Schema constants."""

import rdflib.namespace

__all__ = [
    "bioregistry_schema_terms",
    # Namespaces
    "bioregistry_collection",
    "bioregistry_resource",
    "bioregistry_metaresource",
    "bioregistry_schema",
    "orcid",
]

bioregistry_schema_terms = {
    "Resource": "A type for entries in the Bioregistry's registry.",
    "Registry": "A type for entries in the Bioregistry's metaregistry.",
    "Collection": "A type for entries in the Bioregistry's collections",
    "Mapping": "A type, typically instantiated as a blank node, that connects a given resource to a metaresource"
    " and a metaidentifier using the hasMetaresource and hasMetaidentifier relations.",
    "hasExample": "An identifier for a resource or metaresource.",
    "isProvider": "Denotes whether a metaresource is capable of acting as a provider. If so, should be accompanied"
    ' by a "provider_formatter" relation as well.',
    "isResolver": "Denotes whether a metaresource is capable of acting as a resolver. If so, should be accompanied"
    ' by a "resolver_formatter" relation as well.',
    "hasProviderFormatter": "The URL format for a provider that contains $1 for the identifier (or metaidentifier)"
    " that should be resolved.",
    "hasResolverFormatter": "The URL format for a resolver that contains $1 for the prefix and $2 for the identifier"
    " that should be resolved.",
    "hasPattern": "The pattern for identifiers in the given resource",
    "hasContactEmail": "The email of the contact person for the given resource",
    "hasDownloadURL": "A download link for the given resource",
    "providesFor": "For resources that do not create their own controlled vocabulary, this relation should be used"
    " to point to a different resource that it uses. For example, CTD's gene resource provides for"
    " the NCBI Entres Gene resource.",
    "isDeprecated": "A property whose subject is a resource that denotes if it is still available and usable?"
    " Currently this is a blanket term for decomissioned, unable to locate, abandoned, etc.",
    "hasMapping": "A property whose subject is a resource and object is a mapping",
    "hasRegistry": "A property whose subject is a mapping and object is a metaresource.",
    "hasMetaidentifier": "A property whose subject is a mapping and object is an identifier string.",
}
bioregistry_collection = rdflib.namespace.Namespace("https://bioregistry.io/collection/")
bioregistry_resource = rdflib.namespace.Namespace("https://bioregistry.io/registry/")
bioregistry_metaresource = rdflib.namespace.Namespace("https://bioregistry.io/metaregistry/")
bioregistry_schema = rdflib.namespace.ClosedNamespace(
    "https://bioregistry.io/schema/#",
    terms=sorted(bioregistry_schema_terms),
)
orcid = rdflib.namespace.Namespace("https://orcid.org/")
