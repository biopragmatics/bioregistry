# -*- coding: utf-8 -*-

"""Export the Bioregistry to RDF."""

import os
from io import BytesIO
from typing import Optional

import click
import rdflib
from rdflib import BNode, Literal
from rdflib.namespace import ClosedNamespace, FOAF, Namespace, RDF, RDFS, XSD

import bioregistry
from bioregistry import read_collections, read_metaregistry, read_registry
from bioregistry.constants import DOCS_DATA

bioregistry_collection = Namespace('https://bioregistry.io/collection/')
bioregistry_resource = Namespace('https://bioregistry.io/registry/')
bioregistry_metaresource = Namespace('https://bioregistry.io/metaregistry/')
bioregistry_schema = ClosedNamespace(
    'https://bioregistry.io/schema/#',
    terms=[
        'contains', 'example', 'isRegistry', 'isProvider',
        'isResolver', 'hasAuthor', 'provider_formatter', 'resolver_formatter',
        'pattern', 'email', 'download', 'part_of', 'provides', 'deprecated',
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


def _bind(graph: rdflib.Graph) -> None:
    graph.namespace_manager.bind('bioregistry.resource', bioregistry_resource)
    graph.namespace_manager.bind('bioregistry.metaresource', bioregistry_metaresource)
    graph.namespace_manager.bind('bioregistry.collection', bioregistry_collection)
    graph.namespace_manager.bind('bioregistry.schema', bioregistry_schema)
    graph.namespace_manager.bind('orcid', orcid)
    graph.namespace_manager.bind('foaf', FOAF)


def get_full_rdf() -> rdflib.Graph:
    """Get a combine RDF graph representing the Bioregistry using :mod:`rdflib`."""
    graph = rdflib.Graph()
    _bind(graph)
    _add_metaresources(graph)
    _add_collections(graph)
    _add_resources(graph)

    return graph


def get_resource_rdf(prefix: str) -> rdflib.Graph:
    """Get the RDF for a single resource."""
    graph = rdflib.Graph()
    _bind(graph)
    data = bioregistry.get(prefix)
    if data is None:
        raise KeyError
    _add_resource(graph, prefix, data)
    return graph


def get_resource_rdf_str(prefix: str, fmt: Optional[str] = None) -> str:
    """Get the RDF for a single resource serialized."""
    return _graph_str(get_resource_rdf(prefix), fmt=fmt)


def _graph_str(graph: rdflib.Graph, fmt: Optional[str] = None) -> str:
    stream = BytesIO()
    graph.serialize(stream, format=fmt or 'turtle')
    return stream.getvalue().decode('utf8')


def get_metaresource_rdf(metaprefix: str) -> rdflib.Graph:
    """Get the RDF for a single metaresource."""
    graph = rdflib.Graph()
    _bind(graph)
    data = bioregistry.get_registry(metaprefix)
    if data is None:
        raise KeyError
    _add_metaresource(graph, data)
    return graph


def get_collection_rdf(identifier: str) -> rdflib.Graph:
    """Get the RDF for a single collection."""
    graph = rdflib.Graph()
    _bind(graph)
    data = bioregistry.get_collection(identifier)
    if data is None:
        raise KeyError
    _add_collection(graph, data)
    return graph


def _add_metaresources(graph: rdflib.Graph) -> None:
    for metaresource in read_metaregistry().values():
        _add_metaresource(graph, metaresource)


def _add_collections(graph: rdflib.Graph) -> None:
    for collection in read_collections().values():
        _add_collection(graph, collection)


def _add_resources(graph: rdflib.Graph) -> None:
    for prefix, data in read_registry().items():
        _add_resource(graph, prefix, data)


def _add_collection(graph: rdflib.Graph, data):
    node = bioregistry_collection[data['identifier']]
    graph.add((node, RDF['type'], bioregistry_schema['collection']))
    graph.add((node, RDFS['label'], Literal(data['name'])))
    graph.add((node, RDFS['comment'], Literal(data['description'])))

    for author in data.get('authors', []):
        graph.add((node, bioregistry_schema['hasAuthor'], orcid[author['orcid']]))
        graph.add((orcid[author['orcid']], RDFS['label'], Literal(author['name'])))

    for resource in data['resources']:
        graph.add((node, bioregistry_schema['contains'], bioregistry_resource[resource]))
    return node


def _add_metaresource(graph: rdflib.Graph, data):
    node = bioregistry_metaresource[data['prefix']]
    graph.add((node, RDF['type'], bioregistry_schema['metaresource']))
    graph.add((node, RDFS['label'], Literal(data['name'])))
    graph.add((node, RDFS['comment'], Literal(data['description'])))
    graph.add((node, FOAF['homepage'], Literal(data['homepage'])))
    graph.add((node, bioregistry_schema['example'], Literal(data['example'])))
    graph.add((node, bioregistry_schema['isRegistry'], Literal(data['registry'], datatype=XSD.boolean)))
    graph.add((node, bioregistry_schema['isProvider'], Literal(data['provider'], datatype=XSD.boolean)))
    if data['provider']:
        graph.add((node, bioregistry_schema['provider_formatter'], Literal(data['formatter'])))
    graph.add((node, bioregistry_schema['isResolver'], Literal(data['resolver'], datatype=XSD.boolean)))
    if data['resolver']:
        graph.add((node, bioregistry_schema['resolver_formatter'], Literal(data['resolver_url'])))
    return node


def _add_resource(graph: rdflib.Graph, prefix, data):
    node = bioregistry_resource[prefix]
    graph.add((node, RDF['type'], bioregistry_schema['resource']))
    graph.add((node, RDFS['label'], Literal(bioregistry.get_name(prefix))))
    graph.add((node, RDFS['comment'], Literal(bioregistry.get_description(prefix))))
    graph.add((node, FOAF['homepage'], Literal(bioregistry.get_homepage(prefix))))

    for key, func in [
        ('pattern', bioregistry.get_pattern),
        ('provider_formatter', bioregistry.get_format),
        ('example', bioregistry.get_example),
        ('email', bioregistry.get_email),
    ]:
        value = func(prefix)
        if value is not None:
            graph.add((node, bioregistry_schema[key], Literal(value)))

    download = data.get('download')
    if download:
        graph.add((node, bioregistry_schema['download'], Literal(download)))

    part_of = data.get('part_of')
    if part_of:
        graph.add((node, bioregistry_schema['part_of'], bioregistry_resource[part_of]))

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

    return node


if __name__ == '__main__':
    export_rdf()
