"""Calculate dependencies between resources."""

import tempfile
from collections import Counter
from functools import partial
from pathlib import Path
from typing import NamedTuple

import click
import curies
import obographs
import pandas as pd
import pyobo
import rdflib
import rdflib.exceptions
import robot_obo_tool
import seaborn as sns
from curies import Converter
from curies import vocabulary as v
from pystow.utils import download, name_from_url, read_rdflib, safe_open_writer
from tqdm import tqdm
from tqdm.contrib import tmap
from tqdm.contrib.concurrent import process_map
from tqdm.contrib.logging import logging_redirect_tqdm

from bioregistry import Manager, Resource
from bioregistry.constants import EXPORT_ANALYSES
from bioregistry.schema import AnnotatedURL

USAGE_DIRECTORY = EXPORT_ANALYSES.joinpath("usage")

HERE = Path(__file__).parent.resolve()


class Error(NamedTuple):
    """Contain information about an error."""

    url: str
    format: str | None
    exception: Exception


def _update_resources(
    manager: Manager, results_path: Path, errors_path: Path, *, multiprocessing: bool = False
) -> None:
    converter = manager.get_converter()
    resources = [resource for resource in manager.registry.values() if resource.has_download()]
    _map = partial(process_map, chunksize=30) if multiprocessing else tmap
    with safe_open_writer(results_path) as writer, safe_open_writer(errors_path) as error_writer:
        writer.writerow(("prefix", "uses_prefix"))
        error_writer.writerow(("prefix", *Error._fields))
        for resource, result in _map(
            partial(_process, converter=converter), resources, unit="prefix"
        ):
            match result:
                case None:
                    continue
                case Error(url, format, exception):
                    error_writer.writerow((resource.prefix, url, format or "", str(exception)))
                case set(prefixes):
                    if resource.depends_on is not None:
                        prefixes.update(resource.depends_on)
                    prefixes.discard(resource.prefix)  # don't count self
                    resource.depends_on = sorted(prefixes)
                    for prefix in prefixes:
                        writer.writerow((resource.prefix, prefix))


WIDTH = 15


def _process(
    resource: Resource, *, converter: curies.Converter
) -> tuple[Resource, set[str] | Error | None]:
    if owl := resource.get_download_owl():
        return resource, _get_prefixes_from_owl(resource, owl, converter)
    elif obograph := resource.get_download_obograph():
        return resource, _get_prefixes_from_obograph(resource, obograph, converter)
    elif skos := resource.get_download_skos(get_format=True):
        return resource, _get_prefixes_from_rdf(resource, skos, converter)
    elif rdf := resource.get_download_rdf(get_format=True):
        return resource, _get_prefixes_from_rdf(resource, rdf, converter)
    elif obo := resource.get_download_obo():
        return resource, _get_prefixes_from_owl(resource, obo, converter)
    else:
        return resource, None


def _get_prefixes_from_owl(resource: Resource, url: str, converter: Converter) -> set[str] | Error:
    with logging_redirect_tqdm(), tempfile.TemporaryDirectory() as tmpdir:
        d = Path(tmpdir)
        path = d.joinpath(name_from_url(url))
        ttl_path = d.joinpath("tmp.ttl")
        try:
            download(url=url, path=path, backend="requests")
            robot_obo_tool.convert(path, ttl_path, check=False, fmt="ttl")
            graph = read_rdflib(ttl_path, format="ttl")
        except Exception as e:
            return Error(url, "owl", e)
    return _work_graph(resource, graph, converter)


def _get_prefixes_from_obo(resource: Resource, url: str, converter: Converter) -> set[str] | Error:
    with logging_redirect_tqdm():
        try:
            obo = pyobo.get_ontology(resource.prefix)
        except Exception as e:
            return Error(url, "obo", e)
        else:
            return obo._get_prefixes()


def _get_prefixes_from_obograph(
    resource: Resource, url: str, converter: Converter
) -> set[str] | Error:
    try:
        g = obographs.read(url, squeeze=True)
    except Exception as e:
        return Error(url, "obograph", e)

    prefixes = {
        reference.prefix
        for node in g.nodes
        if (reference := converter.parse_uri(node.id)) is not None
    }
    tqdm.write(
        f"[{resource.prefix:{WIDTH}}] of {len(g.nodes):,} OBO graph nodes, got {len(prefixes)} prefixes"
    )
    return prefixes


def _get_prefixes_from_rdf(
    resource: Resource, rdf: str | AnnotatedURL, converter: Converter
) -> set[str] | Error:
    match rdf:
        case str():
            url = rdf
            rdf_format = None
        case AnnotatedURL() as model:
            url = model.url
            rdf_format = model.rdf_format

    with logging_redirect_tqdm(), tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir).joinpath(name_from_url(url))
        try:
            download(url=url, path=path, backend="requests")
            graph = read_rdflib(path, format=rdf_format)
        except Exception as e:
            return Error(url, rdf_format, e)

    return _work_graph(resource, graph, converter)


PREDI_SKI_OB = {
    v.exact_match,
    v.narrow_match,
    v.broad_match,
    v.close_match,
    v.related_match,
    v.has_dbxref,
}


def _work_graph(resource: Resource, graph: rdflib.Graph, converter: Converter) -> set[str]:
    prefixes = set()
    references = set()
    for s, p, o in tqdm(
        graph.triples((None, None, None)), desc=f"[{resource.prefix}] triples", leave=False
    ):
        if not isinstance(p, rdflib.URIRef):
            keep_object = True
        elif predicate_reference := converter.parse_uri(p):
            keep_object = predicate_reference not in PREDI_SKI_OB
            references.add(predicate_reference)
            prefixes.add(predicate_reference.prefix)
        else:
            keep_object = True
        if isinstance(s, rdflib.URIRef) and (subject_reference := converter.parse_uri(s)):
            references.add(subject_reference)
            prefixes.add(subject_reference.prefix)
        if (
            keep_object
            and isinstance(o, rdflib.URIRef)
            and (object_reference := converter.parse_uri(o))
        ):
            references.add(object_reference)
            prefixes.add(object_reference.prefix)

    tqdm.write(
        f"[{resource.prefix:{WIDTH}}] of {len(references):,} references, got {len(prefixes)} prefixes"
    )
    return prefixes


@click.command()
@click.option("--refresh", is_flag=True)
def main(refresh: bool) -> None:
    results_path = USAGE_DIRECTORY / "results-raw.tsv"
    errors_path = USAGE_DIRECTORY / "errors.tsv"
    if refresh:
        _update_resources(Manager(), results_path, errors_path)

    df = pd.read_csv(results_path, sep="\t", header=None, names=["source", "target"])
    g = sns.countplot(data=df, x="source")
    g.figure.savefig(USAGE_DIRECTORY / "countplot.png")

    # TODO do network-based analysis for transitive closure


if __name__ == "__main__":
    main()
