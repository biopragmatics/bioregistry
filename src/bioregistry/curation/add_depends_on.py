"""Analyze."""

import itertools as itt

import bioregistry
import click
import rdflib
from bioregistry import Resource
from bioregistry.schema import AnnotatedURL
from curies import Converter
from rdflib import OWL, RDF, SKOS
from tabulate import tabulate
from tqdm import tqdm
from tqdm.contrib.logging import logging_redirect_tqdm

from pyobo import Obo
from pyobo.struct.skos import read_skos

SKIPS = {
    # TODO investigate both of these later
    "inspire.theme",
    "infosecsos",
}


def _get_dependencies() -> None:
    converter = bioregistry.get_converter()
    for resource in tqdm(bioregistry.manager.registry.values()):
        if owl := resource.get_download_owl():
            tqdm.write(f"{resource.prefix} skipping OWL for now - {owl}")
        elif rdf := resource.get_download_rdf(get_format=True):
            prefixes = _xx(resource, rdf, converter)
            resource.depends_on = sorted(prefixes) if prefixes else None
        elif skos := resource.get_download_skos(get_format=True):
            prefixes = _xx(resource, skos, converter)
            resource.depends_on = sorted(prefixes) if prefixes else None
        bioregistry.manager.write_registry()


def _xx(resource: Resource, rdf: str | AnnotatedURL, converter: Converter) -> set[str] | None:
    prefixes = set()
    match rdf:
        case str():
            url = rdf
            rdf_format = None
        case AnnotatedURL() as model:
            url = model.url
            rdf_format = model.rdf_format
    graph = _parse(url, rdf_format)
    pr = f"[{resource.prefix}] "
    if isinstance(graph, Exception):
        tqdm.write(pr + click.style(f"failed to parse {url}", fg="red"))
        tqdm.write(str(graph))
        tqdm.write("\n")
        return None

    for node in itt.chain(
        tqdm(graph.subjects(), desc=f"[{resource.prefix}] subjects", leave=False),
        tqdm(graph.predicates(), desc=f"[{resource.prefix}] predicates", leave=False),
        tqdm(graph.objects(), desc=f"[{resource.prefix}] objects", leave=False),
    ):
        if isinstance(node, rdflib.URIRef):
            if reference := converter.parse_uri(str(node)):
                prefixes.add(reference.prefix)
    return prefixes


def _parse(url: str, rdf_format: str | None) -> rdflib.Graph | Exception:
    graph = rdflib.Graph()
    with logging_redirect_tqdm():
        try:
            graph.parse(url, format=rdf_format)
        except Exception as e:
            return e
    return graph


def _annotate_data_models() -> None:
    resources: list[tuple[Resource, str, str | None]] = []
    for resource in bioregistry.manager.registry.values():
        if resource.prefix in SKIPS:
            continue
        if resource.get_download_skos() or resource.get_download_owl():
            continue
        match resource.get_download_rdf(get_format=True):
            case None:
                continue
            case str() as url:
                resources.append((resource, url, None))
            case AnnotatedURL() as model:
                resources.append((resource, model.url, model.rdf_format))

    for resource, url, rdf_format in tqdm(resources, unit="resource"):
        graph = _parse(url, rdf_format)
        pr = f"[{resource.prefix}] "
        if isinstance(graph, Exception):
            tqdm.write(pr + click.style(f"failed to parse {url}", fg="red"))
            tqdm.write(str(graph))
            tqdm.write("\n")
            continue

        owl_top = list(graph.subjects(RDF.type, OWL.Ontology))
        skos_top = list(graph.subjects(RDF.type, SKOS.ConceptScheme))
        if owl_top and skos_top:
            tqdm.write(pr + click.style(f"both SKOS and OWL in {url}", fg="yellow"))
        elif not owl_top and not skos_top:
            tqdm.write(pr + click.style(f"unknown in {url}", fg="yellow"))
        elif len(owl_top) == 1:
            tqdm.write(pr + click.style(f"OWL - {owl_top[0]}", fg="green"))

            # Clear URLs
            resource.download_skos = None
            resource.download_rdf = None
            resource.download_owl = url

        elif len(owl_top) > 1:
            tqdm.write(pr + click.style(f"multiple OWL in {url}", fg="yellow"))
        elif len(skos_top) == 1:
            tqdm.write(pr + click.style(f"SKOS - {skos_top[0]}", fg="green"))

            # Clear URLs
            resource.download_skos = url
            resource.download_rdf = None

        elif len(skos_top) > 1:
            tqdm.write(pr + click.style(f"multiple SKOS in {url}", fg="yellow"))
        else:
            raise RuntimeError

    bioregistry.manager.write_registry()


def _convert_skos() -> None:
    rows = []
    for resource in tqdm(bioregistry.resources()):
        match resource.get_download_skos(get_format=True):
            case None:
                continue
            case str() as url:
                try:
                    ontology = read_skos(url, prefix=resource.prefix)
                except SyntaxError:
                    tqdm.write(f"need explicit RDF format for {resource.prefix}")
                    continue
                rows.append((resource.prefix, url, "", *_summarize(ontology)))
            case AnnotatedURL() as model:
                ontology = read_skos(model.url, prefix=resource.prefix, rdf_format=model.rdf_format)
                rows.append((resource.prefix, model.url, model.rdf_format, *_summarize(ontology)))
        ontology.write_obo(f"/Users/cthoyt/Desktop/{resource.prefix}.obo")

    tqdm.write(tabulate(rows, headers=["prefix", "url", "format", "terms", "parents"]))


def _summarize(ontology: Obo) -> tuple[int, ...]:
    n_parents = 0
    n_terms = 0
    for term in ontology:
        n_terms += 1
        n_parents += len(term.parents)
    return n_terms, n_parents


if __name__ == "__main__":
    _get_dependencies()
