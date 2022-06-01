# -*- coding: utf-8 -*-

"""Export the Bioregistry to RDF."""

import logging
from io import BytesIO
from typing import Any, Callable, List, Optional, Tuple, Union, cast

import click
import rdflib
from rdflib import Literal, Namespace
from rdflib.namespace import DC, DCTERMS, FOAF, RDF, RDFS, SKOS, XSD
from rdflib.term import Node, URIRef

import bioregistry
from bioregistry import manager, read_collections, read_metaregistry, read_registry
from bioregistry.constants import (
    RDF_JSONLD_PATH,
    RDF_NT_PATH,
    RDF_TURTLE_PATH,
    SCHEMA_JSONLD_PATH,
    SCHEMA_NT_PATH,
    SCHEMA_TURTLE_PATH,
)
from bioregistry.export.sssom_export import CURIE_MAP
from bioregistry.schema.constants import (
    bioregistry_collection,
    bioregistry_metaresource,
    bioregistry_resource,
    bioregistry_schema,
    get_schema_rdf,
    orcid,
)
from bioregistry.schema.struct import Collection, Registry

logger = logging.getLogger(__name__)

NAMESPACES = {_ns: Namespace(_uri) for _ns, _uri in CURIE_MAP.items()}
NAMESPACE_WARNINGS = set()


@click.command()
def export_rdf():
    """Export RDF."""
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

    graph = get_full_rdf() + schema_rdf
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


def _graph() -> rdflib.Graph:
    graph = rdflib.Graph()
    _bind(graph)
    return graph


def _bind(graph: rdflib.Graph) -> None:
    graph.namespace_manager.bind("bioregistry", bioregistry_resource)
    graph.namespace_manager.bind("bioregistry.metaresource", bioregistry_metaresource)
    graph.namespace_manager.bind("bioregistry.collection", bioregistry_collection)
    graph.namespace_manager.bind("bioregistry.schema", bioregistry_schema)
    graph.namespace_manager.bind("orcid", orcid)
    graph.namespace_manager.bind("foaf", FOAF)
    graph.namespace_manager.bind("dc", DC)
    graph.namespace_manager.bind("dcterms", DCTERMS)
    for key, value in CURIE_MAP.items():
        graph.namespace_manager.bind(key, value)


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
    graph = _add_resource(data)
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


RESOURCE_FUNCTIONS: List[Tuple[Union[str, URIRef], Callable[[str], Any], URIRef]] = [
    ("0000008", bioregistry.get_pattern, XSD.string),
    ("0000006", bioregistry.get_uri_format, XSD.string),
    ("0000005", bioregistry.get_example, XSD.string),
    ("0000012", bioregistry.is_deprecated, XSD.boolean),
    (DC.description, bioregistry.get_description, XSD.string),
    (FOAF.homepage, bioregistry.get_homepage, XSD.string),
]


def _add_resource(data, *, graph: Optional[rdflib.Graph] = None) -> rdflib.Graph:
    if graph is None:
        graph = _graph()
    prefix = data["prefix"]
    resource = bioregistry.get_resource(prefix)
    if resource is None:
        logger.warning("Could not look up prefix: %s", prefix)
        return graph
    node = cast(URIRef, bioregistry_resource[prefix])
    graph.add((node, RDF.type, bioregistry_schema["0000001"]))
    graph.add((node, RDFS.label, Literal(bioregistry.get_name(prefix))))
    graph.add((node, DCTERMS.isPartOf, bioregistry_metaresource["bioregistry"]))
    graph.add((bioregistry_metaresource["bioregistry"], DCTERMS.hasPart, node))

    for predicate, func, datatype in RESOURCE_FUNCTIONS:
        value = func(prefix)
        if not isinstance(predicate, URIRef):
            predicate = bioregistry_schema[predicate]
        if value is not None:
            graph.add((node, predicate, Literal(value, datatype=datatype)))

    download = data.get("download")
    if download:
        graph.add((node, bioregistry_schema["0000010"], Literal(download)))

    # Ontological relationships

    for depends_on in bioregistry.get_depends_on(prefix) or []:
        graph.add((node, bioregistry_schema["0000017"], bioregistry_resource[depends_on]))

    for appears_in in bioregistry.get_appears_in(prefix) or []:
        graph.add((node, bioregistry_schema["0000018"], bioregistry_resource[appears_in]))

    part_of = bioregistry.get_part_of(prefix)
    if part_of:
        graph.add((node, DCTERMS.isPartOf, bioregistry_resource[part_of]))
        graph.add((bioregistry_resource[part_of], DCTERMS.hasPart, node))

    provides = bioregistry.get_provides_for(prefix)
    if provides:
        graph.add((node, bioregistry_schema["0000011"], bioregistry_resource[provides]))

    canonical = bioregistry.get_has_canonical(prefix)
    if canonical:
        graph.add((node, bioregistry_schema["0000016"], bioregistry_resource[canonical]))

    contact = bioregistry.get_contact(prefix)
    if contact is not None:
        contact_node = contact.add_triples(graph)
        graph.add((node, bioregistry_schema["0000019"], contact_node))
    if resource.reviewer is not None and resource.reviewer.orcid:
        reviewer_node = resource.reviewer.add_triples(graph)
        graph.add((node, bioregistry_schema["0000021"], reviewer_node))
    if resource.contributor is not None and resource.contributor.orcid:
        contributor_node = resource.contributor.add_triples(graph)
        graph.add((contributor_node, DCTERMS.contributor, node))

    mappings = bioregistry.get_mappings(prefix)
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
                bioregistry_metaresource[metaresource.prefix],
            )
        )
        graph.add(
            (
                bioregistry_metaresource[metaresource.prefix],
                DCTERMS.hasPart,
                NAMESPACES[metaprefix][metaidentifier],
            )
        )

    return graph


if __name__ == "__main__":
    export_rdf()
