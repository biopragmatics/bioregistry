# -*- coding: utf-8 -*-

"""Data structures.

.. seealso:: https://pydantic-docs.helpmanual.io/usage/dataclasses/#convert-stdlib-dataclasses-into-pydantic-dataclasses
"""

import json
import pathlib
from typing import Any, List, Mapping, Optional

from pydantic import BaseModel

HERE = pathlib.Path(__file__).parent.resolve()


class Author(BaseModel):
    """Metadata for an author."""

    #: The name of the author
    name: str
    #: The ORCID identifier for the author
    orcid: str


class Resource(BaseModel):
    """Metadata about an ontology, database, or other resource."""

    name: Optional[str]
    description: Optional[str]
    pattern: Optional[str]
    url: Optional[str]
    homepage: Optional[str]
    contact: Optional[str]
    example: Optional[str]
    part_of: Optional[str]
    provides: Optional[str]
    type: Optional[str]
    download: Optional[str]
    banana: Optional[str]
    deprecated: Optional[bool]
    mappings: Optional[Mapping[str, str]]
    synonyms: Optional[List[str]]
    references: Optional[List[str]]
    appears_in: Optional[List[str]]
    ols_version_type: Optional[str]
    ols_version_date_format: Optional[str]
    ols_version_prefix: Optional[str]
    ols_version_suffix_split: Optional[bool]
    namespaceEmbeddedInLui: Optional[bool]  # noqa:N815
    not_available_as_obo: Optional[bool]
    no_own_terms: Optional[bool]
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

    def cdict(self) -> Mapping[str, Any]:
        """Dump as a dict with keys that have null values removed."""
        return {k: v for k, v in self.dict().items() if v is not None}


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
    #: Does this registry have a front-end?
    registry: bool
    #: A URL with a $1 for a prefix to resolve in the registry
    provider_url: Optional[str]
    #: A URL with a $1 for a prefix and $2 for an identifier to resolve in the registry
    resolver_url: Optional[str]


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


def main():
    """Dump the JSON schemata."""
    import pydantic.schema
    top_level_schema = pydantic.schema.schema([Author, Collection, Resource, Registry])
    with HERE.joinpath('schema.json').open('w') as file:
        json.dump(top_level_schema, indent=2, fp=file)


if __name__ == '__main__':
    main()
