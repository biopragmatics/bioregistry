# -*- coding: utf-8 -*-

"""Export the Bioregistry to RDF."""

import os
from io import BytesIO
from typing import Callable, List, Optional, Tuple, Union, cast

import click
import rdflib
from rdflib import BNode, Literal
from rdflib.namespace import DC, DCTERMS, FOAF, RDF, RDFS, XSD
from rdflib.term import Node, URIRef

import bioregistry
from bioregistry import read_collections, read_metaregistry, read_registry
from bioregistry.constants import DOCS_DATA
from bioregistry.schema import (
    Collection,
    Registry,
    bioregistry_collection,
    bioregistry_metaresource,
    bioregistry_resource,
    bioregistry_schema,
    orcid,
)


@click.command()
def export_rdf():
    """Export RDF."""
    graph = get_full_rdf()
    graph.serialize(os.path.join(DOCS_DATA, "bioregistry.ttl"), format="turtle")
    graph.serialize(os.path.join(DOCS_DATA, "bioregistry.nt"), format="nt")
    graph.serialize(os.path.join(DOCS_DATA, "bioregistry.xml"), format="xml")

    context = {
        "@language": "en",
        **dict(graph.namespaces()),
    }
    graph.serialize(
        os.path.join(DOCS_DATA, "bioregistry.jsonld"), format="json-ld", context=context
    )


def _graph() -> rdflib.Graph:
    graph = rdflib.Graph()
    _bind(graph)
    return graph


def _bind(graph: rdflib.Graph) -> None:
    graph.namespace_manager.bind("bioregistry.resource", bioregistry_resource)
    graph.namespace_manager.bind("bioregistry.metaresource", bioregistry_metaresource)
    graph.namespace_manager.bind("bioregistry.collection", bioregistry_collection)
    graph.namespace_manager.bind("bioregistry.schema", bioregistry_schema)
    graph.namespace_manager.bind("orcid", orcid)
    graph.namespace_manager.bind("foaf", FOAF)
    graph.namespace_manager.bind("dc", DC)
    graph.namespace_manager.bind("dcterms", DCTERMS)


def get_full_rdf() -> rdflib.Graph:
    """Get a combine RDF graph representing the Bioregistry using :mod:`rdflib`."""
    graph = _graph()
    _add_metaresources(graph=graph)
    _add_collections(graph=graph)
    _add_resources(graph=graph)
    return graph


def collection_to_rdf_str(data: Union[str, Collection], fmt: Optional[str] = None) -> str:
    """Get a collection as an RDF string."""
    if isinstance(data, str):
        data = bioregistry.get_collection(data)  # type: ignore
        if data is None:
            raise KeyError
    graph, _ = _add_collection(cast(Collection, data))
    return _graph_str(graph, fmt=fmt)


def metaresource_to_rdf_str(data: Union[str, Registry], fmt: Optional[str] = None) -> str:
    """Get a collection as an RDF string."""
    if isinstance(data, str):
        data = bioregistry.get_registry(data)  # type: ignore
        if data is None:
            raise KeyError
    graph, _ = _add_metaresource(cast(Registry, data))
    return _graph_str(graph, fmt=fmt)


def resource_to_rdf_str(data, fmt: Optional[str] = None) -> str:
    """Get a collection as an RDF string."""
    if isinstance(data, str):
        data = {"prefix": data, **bioregistry.get_resource(data).dict()}  # type: ignore
    graph, _ = _add_resource(data)
    return _graph_str(graph, fmt=fmt)


def _graph_str(graph: rdflib.Graph, fmt: Optional[str] = None) -> str:
    stream = BytesIO()
    graph.serialize(stream, format=fmt or "turtle")
    return stream.getvalue().decode("utf8")


def _add_metaresources(*, graph: Optional[rdflib.Graph] = None) -> rdflib.Graph:
    if graph is None:
        graph = _graph()
    for data in read_metaregistry().values():
        _add_metaresource(graph=graph, data=data)
    return graph


def _add_collections(*, graph: Optional[rdflib.Graph] = None) -> rdflib.Graph:
    if graph is None:
        graph = _graph()
    for collection in read_collections().values():
        _add_collection(graph=graph, data=collection)
    return graph


def _add_resources(*, graph: Optional[rdflib.Graph] = None) -> rdflib.Graph:
    if graph is None:
        graph = _graph()
    for prefix, data in read_registry().items():
        _add_resource(graph=graph, data={"prefix": prefix, **data.dict()})
    return graph


def _add_collection(
    data: Collection, *, graph: Optional[rdflib.Graph] = None
) -> Tuple[rdflib.Graph, Node]:
    if graph is None:
        graph = _graph()
    node = data.add_triples(graph)
    return graph, node


def _add_metaresource(
    data: Registry, *, graph: Optional[rdflib.Graph] = None
) -> Tuple[rdflib.Graph, Node]:
    if graph is None:
        graph = _graph()
    node = data.add_triples(graph)
    return graph, node


RESOURCE_FUNCTIONS: List[Tuple[str, Callable[[str], Optional[str]]]] = [
    ("hasPattern", bioregistry.get_pattern),
    ("hasProviderFormatter", bioregistry.get_format),
    ("hasExample", bioregistry.get_example),
    ("hasContactEmail", bioregistry.get_email),
]


def _add_resource(data, *, graph: Optional[rdflib.Graph] = None) -> Tuple[rdflib.Graph, Node]:
    if graph is None:
        graph = _graph()
    prefix = data["prefix"]
    node = cast(URIRef, bioregistry_resource[prefix])
    graph.add((node, RDF["type"], bioregistry_schema["Resource"]))
    graph.add((node, RDFS["label"], Literal(bioregistry.get_name(prefix))))

    for key, func in RESOURCE_FUNCTIONS:
        value = func(prefix)
        if value is not None:
            graph.add((node, bioregistry_schema[key], Literal(value)))

    for rel, func in [
        (DC.description, bioregistry.get_description),
        (FOAF.homepage, bioregistry.get_homepage),
    ]:
        value = func(prefix)
        if value is not None:
            graph.add((node, rel, Literal(value)))

    download = data.get("download")
    if download:
        graph.add((node, bioregistry_schema["hasDownloadURL"], Literal(download)))

    part_of = data.get("part_of")
    if part_of:
        graph.add((node, DCTERMS.isPartOf, bioregistry_resource[part_of]))
        graph.add((bioregistry_resource[part_of], DCTERMS.hasPart, node))

    provides = data.get("provides")
    if provides:
        graph.add((node, bioregistry_schema["providesFor"], bioregistry_resource[provides]))

    graph.add(
        (
            node,
            bioregistry_schema["isDeprecated"],
            Literal(bioregistry.is_deprecated(prefix), datatype=XSD.boolean),
        )
    )

    mappings = bioregistry.get_mappings(prefix)
    for metaprefix, metaidentifier in (mappings or {}).items():
        mapping_node = BNode()
        graph.add((node, bioregistry_schema["hasMapping"], mapping_node))
        graph.add((mapping_node, RDF["type"], bioregistry_schema["Mapping"]))
        graph.add(
            (mapping_node, bioregistry_schema["hasRegistry"], bioregistry_metaresource[metaprefix])
        )
        graph.add((mapping_node, bioregistry_schema["hasMetaidentifier"], Literal(metaidentifier)))

    return graph, node


if __name__ == "__main__":
    export_rdf()
