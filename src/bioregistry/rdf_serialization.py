from io import BytesIO
from pprint import pprint

import rdflib
from rdflib import Literal, Namespace, RDFS

from bioregistry import get, get_registry, read_collections, read_metaregistry

bioregistry_collection = Namespace('https://bioregistry.io/collection/')
bioregistry_resource = Namespace('https://bioregistry.io/registry/')
bioregistry_metaresource = Namespace('https://bioregistry.io/metaregistry/')
bioregistry_schema = Namespace('https://bioregistry.io/schema/#')
orcid = Namespace('https://orcid.org/')


def get_graph() -> rdflib.Graph:
    graph = rdflib.Graph()
    graph.namespace_manager.bind('bioregistry.resource', bioregistry_resource)
    graph.namespace_manager.bind('bioregistry.metaresource', bioregistry_metaresource)
    graph.namespace_manager.bind('bioregistry.collection', bioregistry_collection)
    graph.namespace_manager.bind('bioregistry.schema', bioregistry_schema)
    graph.namespace_manager.bind('orcid', orcid)

    k = list(read_metaregistry())[0]
    mr = get_registry(k)
    pprint(mr)
    _add_metaresource(graph, mr)
    # add_collections(graph)

    return graph


def add_collections(graph: rdflib.Graph):
    for collection in read_collections().values():
        _add_collection(graph, collection)


def _add_collection(graph: rdflib.Graph, collection):
    node = bioregistry_collection[collection['identifier']]
    graph.add((node, RDFS['label'], Literal(collection['name'])))
    graph.add((node, RDFS['comment'], Literal(collection['description'])))

    for author in collection.get('authors', []):
        graph.add((node, bioregistry_schema['hasAuthor'], orcid[author['orcid']]))
        graph.add((orcid[author['orcid']], RDFS['label'], Literal(author['name'])))

    for resource in collection['resources']:
        graph.add((node, bioregistry_schema['contains'], bioregistry_resource[resource]))


def get_registry_triples(metaprefix):
    registry = get_registry(metaprefix)
    if registry is None:
        raise KeyError


def _add_metaresource(graph: rdflib.Graph, metaresource):
    node = bioregistry_metaresource[metaresource['prefix']]
    graph.add((node, RDFS['label'], Literal(metaresource['name'])))
    graph.add((node, RDFS['comment'], Literal(metaresource['description'])))


def resource_triples(prefix):
    resource = get(prefix)
    if resource is None:
        raise KeyError


def main():
    graph = get_graph()
    stream = BytesIO()
    graph.serialize(stream, format='turtle')
    print(stream.getvalue().decode('utf8'))


if __name__ == '__main__':
    main()
