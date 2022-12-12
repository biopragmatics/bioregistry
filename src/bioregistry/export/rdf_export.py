# -*- coding: utf-8 -*-

"""Export the Bioregistry to RDF."""

import logging
from typing import Any, Callable, List, Optional, Tuple, Union, cast

import click
import rdflib
from rdflib import Literal, Namespace
from rdflib.namespace import DC, DCTERMS, FOAF, RDF, RDFS, SKOS, XSD
from rdflib.term import Node, URIRef

from bioregistry import Manager, manager
from bioregistry.constants import (
    RDF_JSONLD_PATH,
    RDF_NT_PATH,
    RDF_TURTLE_PATH,
    SCHEMA_JSONLD_PATH,
    SCHEMA_NT_PATH,
    SCHEMA_TURTLE_PATH,
)
from bioregistry.schema.constants import (
    BR_COLLECTION,
    BR_METARESOURCE,
    BR_RESOURCE,
    BR_SCHEMA,
    get_schema_rdf,
    orcid,
)
from bioregistry.schema.struct import Collection, Registry, Resource

logger = logging.getLogger(__name__)

NAMESPACES = {_ns: Namespace(_uri) for _ns, _uri in manager.get_internal_prefix_map().items()}
NAMESPACE_WARNINGS = set()


@click.command()
def export_rdf():
    """Export RDF."""
    from bioregistry import manager

    schema_rdf = get_schema_rdf()
    schema_rdf.serialize(SCHEMA_TURTLE_PATH.as_posix(), format="turtle")
    schema_rdf.serialize(SCHEMA_NT_PATH.as_posix(), format="nt", encoding="utf-8")
    schema_rdf.serialize(
        SCHEMA_JSONLD_PATH.as_posix(),
        format="json-ld",
        context={
            "@language": "en",
            **dict(schema_rdf.namespaces()),
        },
        sort_keys=True,
        ensure_ascii=False,
    )

    graph = get_full_rdf(manager=manager) + schema_rdf
    graph.serialize(RDF_TURTLE_PATH.as_posix(), format="turtle")
    graph.serialize(RDF_NT_PATH.as_posix(), format="nt", encoding="utf-8")
    # Currently getting an issue with not being able to shorten URIs
    # graph.serialize(os.path.join(DOCS_DATA, "bioregistry.xml"), format="xml")

    context = {
        "@language": "en",
        **dict(graph.namespaces()),
    }
    graph.serialize(
        RDF_JSONLD_PATH.as_posix(),
        format="json-ld",
        context=context,
        sort_keys=True,
        ensure_ascii=False,
    )


def _graph(manager: Manager) -> rdflib.Graph:
    graph = rdflib.Graph()
    _bind(graph=graph, manager=manager)
    return graph


def _bind(graph: rdflib.Graph, manager: Manager) -> None:
    graph.namespace_manager.bind("bioregistry", BR_RESOURCE)
    graph.namespace_manager.bind("bioregistry.metaresource", BR_METARESOURCE)
    graph.namespace_manager.bind("bioregistry.collection", BR_COLLECTION)
    graph.namespace_manager.bind("bioregistry.schema", BR_SCHEMA)
    graph.namespace_manager.bind("orcid", orcid)
    graph.namespace_manager.bind("foaf", FOAF)
    graph.namespace_manager.bind("dc", DC)
    graph.namespace_manager.bind("dcterms", DCTERMS)
    graph.namespace_manager.bind("skos", SKOS)
    for key, value in manager.get_internal_prefix_map().items():
        graph.namespace_manager.bind(key, value)


def get_full_rdf(manager: Manager) -> rdflib.Graph:
    """Get a combine RDF graph representing the Bioregistry using :mod:`rdflib`."""
    graph = _graph(manager=manager)
    for registry in manager.metaregistry.values():
        _add_metaresource(graph=graph, registry=registry)
    for collection in manager.collections.values():
        _add_collection(graph=graph, data=collection)
    for resource in manager.registry.values():
        _add_resource(graph=graph, manager=manager, resource=resource)
    return graph


def collection_to_rdf_str(
    collection: Union[str, Collection],
    manager: Manager,
    fmt: Optional[str] = None,
    encoding: Optional[str] = None,
) -> Union[str, bytes]:
    """Get a collection as an RDF string."""
    if isinstance(collection, str):
        collection = manager.collections[collection]
    graph = _graph(manager=manager)
    _add_collection(cast(Collection, collection), graph=graph)
    return graph.serialize(format=fmt or "turtle", encoding=encoding)


def metaresource_to_rdf_str(
    registry: Union[str, Registry],
    manager: Manager,
    fmt: Optional[str] = None,
    encoding: Optional[str] = None,
) -> str:
    """Get a collection as an RDF string."""
    if isinstance(registry, str):
        registry = manager.metaregistry[registry]
    graph = _graph(manager=manager)
    _add_metaresource(cast(Registry, registry), graph=graph)
    return graph.serialize(format=fmt or "turtle", encoding=encoding)


def resource_to_rdf_str(
    resource: Union[str, Resource],
    manager: Manager,
    fmt: Optional[str] = None,
    encoding: Optional[str] = None,
) -> Union[str, bytes]:
    """Get a collection as an RDF string."""
    if isinstance(resource, str):
        resource = manager.registry[resource]
    graph = _graph(manager=manager)
    _add_resource(cast(Resource, resource), manager=manager, graph=graph)
    return graph.serialize(format=fmt or "turtle", encoding=encoding)


def _add_collection(data: Collection, *, graph: rdflib.Graph) -> Tuple[rdflib.Graph, Node]:
    node = data.add_triples(graph)
    return graph, node


def _add_metaresource(registry: Registry, *, graph: rdflib.Graph) -> Tuple[rdflib.Graph, Node]:
    node = registry.add_triples(graph)
    return graph, node


def _get_resource_functions(
    manager: Manager,
) -> List[Tuple[Union[str, URIRef], Callable[[str], Any], URIRef]]:
    return [
        ("0000008", manager.get_pattern, XSD.string),
        ("0000006", manager.get_uri_format, XSD.string),
        ("0000005", manager.get_example, XSD.string),
        ("0000012", manager.is_deprecated, XSD.boolean),
        (DC.description, manager.get_description, XSD.string),
        (FOAF.homepage, manager.get_homepage, XSD.string),
    ]


def _add_resource(resource: Resource, *, manager: Manager, graph: rdflib.Graph):
    node = cast(URIRef, BR_RESOURCE[resource.prefix])
    graph.add((node, RDF.type, BR_SCHEMA["0000001"]))
    graph.add((node, RDFS.label, Literal(resource.get_name())))
    graph.add((node, DCTERMS.isPartOf, BR_METARESOURCE["bioregistry"]))
    graph.add((BR_METARESOURCE["bioregistry"], DCTERMS.hasPart, node))

    for predicate, func, datatype in _get_resource_functions(manager):
        value = func(resource.prefix)
        if not isinstance(predicate, URIRef):
            predicate = BR_SCHEMA[predicate]
        if value is not None:
            graph.add((node, predicate, Literal(value, datatype=datatype)))

    download = (
        resource.get_download_owl()
        or resource.get_download_obo()
        or resource.get_download_obograph()
    )
    if download:
        graph.add((node, BR_SCHEMA["0000010"], URIRef(download)))

    # Ontological relationships

    for depends_on in manager.get_depends_on(resource.prefix) or []:
        graph.add((node, BR_SCHEMA["0000017"], BR_RESOURCE[depends_on]))

    for appears_in in manager.get_appears_in(resource.prefix) or []:
        graph.add((node, BR_SCHEMA["0000018"], BR_RESOURCE[appears_in]))

    part_of = manager.get_part_of(resource.prefix)
    if part_of:
        graph.add((node, DCTERMS.isPartOf, BR_RESOURCE[part_of]))
        graph.add((BR_RESOURCE[part_of], DCTERMS.hasPart, node))

    provides = manager.get_provides_for(resource.prefix)
    if provides:
        graph.add((node, BR_SCHEMA["0000011"], BR_RESOURCE[provides]))

    if resource.has_canonical:
        graph.add((node, BR_SCHEMA["0000016"], BR_RESOURCE[resource.has_canonical]))

    contact = resource.get_contact()
    if contact is not None:
        contact_node = contact.add_triples(graph)
        graph.add((node, BR_SCHEMA["0000019"], contact_node))
    if resource.reviewer is not None and resource.reviewer.orcid:
        reviewer_node = resource.reviewer.add_triples(graph)
        graph.add((node, BR_SCHEMA["0000021"], reviewer_node))
    if resource.contributor is not None and resource.contributor.orcid:
        contributor_node = resource.contributor.add_triples(graph)
        graph.add((contributor_node, DCTERMS.contributor, node))

    mappings = resource.get_mappings()
    for metaprefix, metaidentifier in (mappings or {}).items():
        metaresource = manager.metaregistry[metaprefix]
        if metaprefix not in NAMESPACES and metaresource.bioregistry_prefix in NAMESPACES:
            metaprefix = metaresource.bioregistry_prefix
        if metaprefix not in NAMESPACES:
            if metaprefix not in NAMESPACE_WARNINGS:
                logger.warning(f"can not find prefix-uri pair for {metaprefix}")
                NAMESPACE_WARNINGS.add(metaprefix)
            continue
        graph.add((node, SKOS.exactMatch, NAMESPACES[metaprefix][metaidentifier]))
        graph.add(
            (
                NAMESPACES[metaprefix][metaidentifier],
                DCTERMS.isPartOf,
                BR_METARESOURCE[metaresource.prefix],
            )
        )
        graph.add(
            (
                BR_METARESOURCE[metaresource.prefix],
                DCTERMS.hasPart,
                NAMESPACES[metaprefix][metaidentifier],
            )
        )


if __name__ == "__main__":
    export_rdf()
