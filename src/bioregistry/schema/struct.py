# -*- coding: utf-8 -*-

"""Data structures.

.. seealso:: https://pydantic-docs.helpmanual.io/usage/dataclasses/#convert-stdlib-dataclasses-into-pydantic-dataclasses
"""

import json
import pathlib
from functools import lru_cache
from typing import Any, Dict, List, Mapping, Optional, Sequence

import pydantic.schema
import rdflib
from pydantic import BaseModel
from rdflib import Literal
from rdflib.namespace import DC, DCTERMS, FOAF, RDF, RDFS, XSD
from rdflib.term import Node

from bioregistry.schema.constants import (
    bioregistry_collection,
    bioregistry_metaresource,
    bioregistry_resource,
    bioregistry_schema,
    orcid,
)

HERE = pathlib.Path(__file__).parent.resolve()


def sanitize_model(base_model: BaseModel) -> Mapping[str, Any]:
    """Sanitize a single pydantic model."""
    return {key: value for key, value in base_model.dict().items() if value is not None}


def sanitize_mapping(mapping: Mapping[str, BaseModel]) -> Mapping[str, Mapping[str, Any]]:
    """Sanitize a pydantic dictionary."""
    return {key: sanitize_model(base_model) for key, base_model in mapping.items()}


class Author(BaseModel):
    """Metadata for an author."""

    #: The name of the author
    name: str
    #: The ORCID identifier for the author
    orcid: str
    #: The email for the author
    email: Optional[str]

    def add_triples(self, graph: rdflib.Graph) -> Node:
        """Add triples to an RDF graph for this collection."""
        node = orcid.term(self.orcid)
        graph.add((node, RDFS["label"], Literal(self.name)))
        return node


class Resource(BaseModel):
    """Metadata about an ontology, database, or other resource."""

    #: The human-readable name of the resource
    name: Optional[str]
    #: A description of the resource
    description: Optional[str]
    #: The regular expression pattern for identifiers in the resource
    pattern: Optional[str]
    #: The format URL, which must have at least one "$1" in it
    url: Optional[str]
    #: The home page for the resource
    homepage: Optional[str]
    #: The contact email address for the resource
    contact: Optional[str]
    #: An example identifier for the resource
    example: Optional[str]
    #: Another bioregistry prefix denoting which resource this one is a part of
    #: (e.g., chembl.compound is part of chembl)
    part_of: Optional[str]
    #: Another bioregistry prefix denoting that this resource provides for another
    #: (e.g., ctd.gene provides for ncbigene)
    provides: Optional[str]
    #: The resource type TODO
    type: Optional[str]
    #: A URL to download this resource as OWL
    download_owl: Optional[str]
    #: A URL to download this resource as OBO
    download_obo: Optional[str]
    #: The redundant prefix that may appear in identifiers (e.g., "FBbt:")
    banana: Optional[str]
    #: A flag to note if this resource is deprecated - will override OLS, OBO Foundry, and prefixcommons notes
    deprecated: Optional[bool]
    #: A dictionary of metaprefixes to prefixes in external registries
    mappings: Optional[Dict[str, str]]
    #: A list of synonyms for the prefix of this resource
    synonyms: Optional[List[str]]
    #: A list of URLs to also see
    references: Optional[List[str]]
    #: A list of prefixes that use this resource for xrefs, provenance, etc.
    appears_in: Optional[List[str]]
    #: A flag denoting if the namespace is embedded in the LUI (if this is true and it is not accompanied by a banana,
    #: assume that the banana is the prefix in all caps plus a colon, as is standard in OBO)
    namespaceEmbeddedInLui: Optional[bool]  # noqa:N815
    #: A flag to denote if the resource is not available as OBO TODO remove this
    not_available_as_obo: Optional[bool]
    #: A flag to denote if the resource does not have any identifiers itself
    no_own_terms: Optional[bool]
    #: Free text comment
    comment: Optional[str]

    # Registry-specific data
    miriam: Optional[Mapping[str, Any]]
    n2t: Optional[Mapping[str, Any]]
    prefixcommons: Optional[Mapping[str, Any]]
    wikidata: Optional[Mapping[str, Any]]
    go: Optional[Mapping[str, Any]]
    obofoundry: Optional[Mapping[str, Any]]
    bioportal: Optional[Mapping[str, Any]]
    ols: Optional[Mapping[str, Any]]
    ncbi: Optional[Mapping[str, Any]]
    uniprot: Optional[Mapping[str, Any]]
    biolink: Optional[Mapping[str, Any]]

    def get_external(self, metaprefix) -> Mapping[str, Any]:
        """Get an external registry."""
        return self.dict().get(metaprefix) or dict()

    def get_prefix_key(self, key: str, metaprefixes: Sequence[str]):
        """Get a key enriched by the given external resources' data."""
        rv = self.dict().get(key)
        if rv is not None:
            return rv
        for metaprefix in metaprefixes:
            external = self.get_external(metaprefix)
            if external is None:
                raise TypeError
            rv = external.get(key)
            if rv is not None:
                return rv
        return None

    def get_default_url(self, identifier: str) -> Optional[str]:
        """Return the default URL for the identifier."""
        if self.url is None:
            return None
        return self.url.replace("$1", identifier)

    def __setitem__(self, key, value):  # noqa: D105
        setattr(self, key, value)


class Registry(BaseModel):
    """Metadata about a registry."""

    #: The registry's metaprefix
    prefix: str
    #: The name of the registry
    name: str
    #: A description of the registry
    description: str
    #: The registry's homepage
    homepage: str
    #: An example prefix in the registry
    example: str
    #: A URL to download the registry's contents
    download: Optional[str]
    #: Does this registry act as a provider (for the prefixes it lists)?
    provider: bool
    #: Does this registry act as a resolver for its prefixes and their respective identifiers?
    resolver: bool
    #: A URL with a $1 for a prefix to resolve in the registry
    provider_url: Optional[str]
    #: A URL with a $1 for a prefix and $2 for an identifier to resolve in the registry
    resolver_url: Optional[str]
    #: An optional contact email
    contact: Optional[str]

    def get_provider(self, metaidentifier: str) -> Optional[str]:
        """Get the provider string."""
        provider_url = self.provider_url
        if provider_url is None:
            return None
        return provider_url.replace("$1", metaidentifier)

    def add_triples(self, graph: rdflib.Graph) -> Node:
        """Add triples to an RDF graph for this registry."""
        node = bioregistry_metaresource.term(self.prefix)
        graph.add((node, RDF["type"], bioregistry_schema[self.__class__.__name__]))
        graph.add((node, RDFS["label"], Literal(self.name)))
        graph.add((node, DC.description, Literal(self.description)))
        graph.add((node, FOAF["homepage"], Literal(self.homepage)))
        graph.add((node, bioregistry_schema["hasExample"], Literal(self.example)))
        graph.add(
            (node, bioregistry_schema["isProvider"], Literal(self.provider, datatype=XSD.boolean))
        )
        graph.add(
            (node, bioregistry_schema["isResolver"], Literal(self.resolver, datatype=XSD.boolean))
        )
        if self.provider_url:
            graph.add(
                (node, bioregistry_schema["hasProviderFormatter"], Literal(self.provider_url))
            )
        if self.resolver_url:
            graph.add(
                (node, bioregistry_schema["hasResolverFormatter"], Literal(self.resolver_url))
            )
        return node


class Collection(BaseModel):
    """A collection of resources."""

    #: The collection's identifier, matching regex ^\d{7}$
    identifier: str
    #: The name of the collection
    name: str
    #: A description of the collection
    description: str
    #: A list of the resources' prefixes appearing in the collection
    resources: List[str]
    #: Authors/contributors to the collection
    authors: List[Author]
    #: JSON-LD context name
    context: Optional[str]

    def add_triples(self, graph: rdflib.Graph) -> Node:
        """Add triples to an RDF graph for this collection."""
        node = bioregistry_collection.term(self.identifier)
        graph.add((node, RDF["type"], bioregistry_schema[self.__class__.__name__]))
        graph.add((node, RDFS["label"], Literal(self.name)))
        graph.add((node, DC.description, Literal(self.description)))

        for author in self.authors:
            author_node = author.add_triples(graph)
            graph.add((node, DC.creator, author_node))

        for resource in self.resources:
            graph.add((node, DCTERMS.hasPart, bioregistry_resource[resource]))

        return node

    def as_context_jsonld(self) -> Mapping[str, Mapping[str, str]]:
        """Get the JSON-LD context from a given collection."""
        return {
            "@context": self.as_prefix_map(),
        }

    def as_prefix_map(self) -> Mapping[str, str]:
        """Get the prefix map for a given collection."""
        from ..resolve import get_format_url

        rv = {}
        for prefix in self.resources:
            fmt = get_format_url(prefix)
            if fmt is not None:
                rv[prefix] = fmt
        return rv


@lru_cache(maxsize=1)
def get_json_schema():
    """Get the JSON schema for the bioregistry."""
    rv = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "$id": "https://bioregistry.io/schema.json",
    }
    rv.update(
        pydantic.schema.schema(
            [
                Author,
                Collection,
                Resource,
                Registry,
            ]
        )
    )
    return rv


def main():
    """Dump the JSON schemata."""
    with HERE.joinpath("schema.json").open("w") as file:
        json.dump(get_json_schema(), indent=2, fp=file)


if __name__ == "__main__":
    main()
