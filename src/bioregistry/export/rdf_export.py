# -*- coding: utf-8 -*-

"""Export the Bioregistry to RDF."""

import os
from io import BytesIO
from typing import Optional, Tuple, cast

import click
import rdflib
from rdflib import BNode, Literal
from rdflib.namespace import ClosedNamespace, DC, DCTERMS, FOAF, Namespace, RDF, RDFS, XSD
from rdflib.term import Node, URIRef

import bioregistry
from bioregistry import read_collections, read_metaregistry, read_registry
from bioregistry.constants import DOCS_DATA

bioregistry_collection = Namespace('https://bioregistry.io/collection/')
bioregistry_resource = Namespace('https://bioregistry.io/registry/')
bioregistry_metaresource = Namespace('https://bioregistry.io/metaregistry/')
bioregistry_schema = ClosedNamespace(
    'https://bioregistry.io/schema/#',
    terms=[
        'example', 'isRegistry', 'isProvider',
        'isResolver', 'provider_formatter', 'resolver_formatter',
        'pattern', 'email', 'download', 'provides', 'deprecated',
        'hasMetaresource', 'hasMetaidentifier', 'mapping', 'hasMapping',
        'resource', 'metaresource', 'collection',
    ],
)
orcid = Namespace('https://orcid.org/')


@click.command()
def export_rdf():
    """Export RDF."""
    graph = get_full_rdf()
    graph.serialize(os.path.join(DOCS_DATA, 'bioregistry.ttl'), format='turtle')
    graph.serialize(os.path.join(DOCS_DATA, 'bioregistry.nt'), format='nt')
    graph.serialize(os.path.join(DOCS_DATA, 'bioregistry.xml'), format='xml')

    context = {
        "@language": "en",
        **dict(graph.namespaces()),
    }
    graph.serialize(os.path.join(DOCS_DATA, 'bioregistry.jsonld'), format='json-ld', context=context)


def _graph() -> rdflib.Graph:
    graph = rdflib.Graph()
    _bind(graph)
    return graph


def _bind(graph: rdflib.Graph) -> None:
    graph.namespace_manager.bind('bioregistry.resource', bioregistry_resource)
    graph.namespace_manager.bind('bioregistry.metaresource', bioregistry_metaresource)
    graph.namespace_manager.bind('bioregistry.collection', bioregistry_collection)
    graph.namespace_manager.bind('bioregistry.schema', bioregistry_schema)
    graph.namespace_manager.bind('orcid', orcid)
    graph.namespace_manager.bind('foaf', FOAF)
    graph.namespace_manager.bind('dc', DC)
    graph.namespace_manager.bind('dcterms', DCTERMS)


def get_full_rdf() -> rdflib.Graph:
    """Get a combine RDF graph representing the Bioregistry using :mod:`rdflib`."""
    graph = _graph()
    _add_metaresources(graph=graph)
    _add_collections(graph=graph)
    _add_resources(graph=graph)
    return graph


def collection_to_rdf_str(data, fmt: Optional[str] = None) -> str:
    """Get a collection as an RDF string."""
    if isinstance(data, str):
        data = bioregistry.get_collection(data)
    graph, _ = _add_collection(data)
    return _graph_str(graph, fmt=fmt)


def metaresource_to_rdf_str(data, fmt: Optional[str] = None) -> str:
    """Get a collection as an RDF string."""
    if isinstance(data, str):
        data = bioregistry.get_registry(data)
    graph, _ = _add_metaresource(data)
    return _graph_str(graph, fmt=fmt)


def resource_to_rdf_str(data, fmt: Optional[str] = None) -> str:
    """Get a collection as an RDF string."""
    if isinstance(data, str):
        data = bioregistry.get(data)
    graph, _ = _add_resource(data=data)
    return _graph_str(graph, fmt=fmt)


def _graph_str(graph: rdflib.Graph, fmt: Optional[str] = None) -> str:
    stream = BytesIO()
    graph.serialize(stream, format=fmt or 'turtle')
    return stream.getvalue().decode('utf8')


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
        _add_resource(graph=graph, data={'prefix': prefix, **data})
    return graph


def _add_collection(data, *, graph: Optional[rdflib.Graph] = None) -> Tuple[rdflib.Graph, Node]:
    if graph is None:
        graph = _graph()
    node = cast(URIRef, bioregistry_collection[data['identifier']])
    graph.add((node, RDF['type'], bioregistry_schema['collection']))
    graph.add((node, RDFS['label'], Literal(data['name'])))
    graph.add((node, DC.description, Literal(data['description'])))

    for author in data.get('authors', []):
        graph.add((node, DC.creator, orcid[author['orcid']]))
        graph.add((orcid[author['orcid']], RDFS['label'], Literal(author['name'])))

    for resource in data['resources']:
        graph.add((node, DCTERMS.hasPart, bioregistry_resource[resource]))

    return graph, node


def _add_metaresource(data, *, graph: Optional[rdflib.Graph] = None) -> Tuple[rdflib.Graph, Node]:
    if graph is None:
        graph = _graph()
    node = cast(URIRef, bioregistry_metaresource[data['prefix']])
    graph.add((node, RDF['type'], bioregistry_schema['metaresource']))
    graph.add((node, RDFS['label'], Literal(data['name'])))
    graph.add((node, DC.description, Literal(data['description'])))
    graph.add((node, FOAF['homepage'], Literal(data['homepage'])))
    graph.add((node, bioregistry_schema['example'], Literal(data['example'])))
    graph.add((node, bioregistry_schema['isRegistry'], Literal(data['registry'], datatype=XSD.boolean)))
    graph.add((node, bioregistry_schema['isProvider'], Literal(data['provider'], datatype=XSD.boolean)))
    if data['provider']:
        graph.add((node, bioregistry_schema['provider_formatter'], Literal(data['formatter'])))
    graph.add((node, bioregistry_schema['isResolver'], Literal(data['resolver'], datatype=XSD.boolean)))
    if data['resolver']:
        graph.add((node, bioregistry_schema['resolver_formatter'], Literal(data['resolver_url'])))
    return graph, node


def _add_resource(data, *, graph: Optional[rdflib.Graph] = None) -> Tuple[rdflib.Graph, Node]:
    if graph is None:
        graph = _graph()
    prefix = data['prefix']
    node = cast(URIRef, bioregistry_resource[prefix])
    graph.add((node, RDF['type'], bioregistry_schema['resource']))
    graph.add((node, RDFS['label'], Literal(bioregistry.get_name(prefix))))

    for key, func in [
        ('pattern', bioregistry.get_pattern),
        ('provider_formatter', bioregistry.get_format),
        ('example', bioregistry.get_example),
        ('email', bioregistry.get_email),
    ]:
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

    download = data.get('download')
    if download:
        graph.add((node, bioregistry_schema['download'], Literal(download)))

    part_of = data.get('part_of')
    if part_of:
        graph.add((node, DCTERMS.isPartOf, bioregistry_resource[part_of]))
        graph.add((bioregistry_resource[part_of], DCTERMS.hasPart, node))

    provides = data.get('provides')
    if provides:
        graph.add((node, bioregistry_schema['provides'], bioregistry_resource[provides]))

    graph.add((
        node,
        bioregistry_schema['deprecated'],
        Literal(bioregistry.is_deprecated(prefix), datatype=XSD.boolean),
    ))

    mappings = bioregistry.get_mappings(prefix)
    for metaprefix, metaidentifier in (mappings or {}).items():
        mapping_node = BNode()
        graph.add((node, bioregistry_schema['hasMapping'], mapping_node))
        graph.add((mapping_node, RDF['type'], bioregistry_schema['mapping']))
        graph.add((mapping_node, bioregistry_schema['hasMetaresource'], bioregistry_metaresource[metaprefix]))
        graph.add((mapping_node, bioregistry_schema['hasMetaidentifier'], Literal(metaidentifier)))

    return graph, node


if __name__ == '__main__':
    export_rdf()
