"""Generating records for :mod:`curies`."""

from __future__ import annotations

import itertools as itt
import logging
from collections import defaultdict
from collections.abc import Collection, Iterable, Mapping, Sequence
from typing import Literal, cast, overload

import curies
from curies import Converter, Record
from curies.w3c import NCNAME_RE

from .schema import Resource

__all__ = [
    "get_converter",
]

logger = logging.getLogger(__name__)
prefix_blacklist = {"bgee.gene"}
uri_prefix_blacklist = {
    "http://www.ebi.ac.uk/ontology-lookup/?termId=",
    "https://www.ebi.ac.uk/ontology-lookup/?termId=",
    "https://purl.obolibrary.org/obo/",
    "http://purl.obolibrary.org/obo/",
    # see https://github.com/biopragmatics/bioregistry/issues/548
    "https://www.ncbi.nlm.nih.gov/nuccore/",
    "http://www.ncbi.nlm.nih.gov/nuccore/",
    "https://www.ebi.ac.uk/ena/data/view/",
    "http://www.ebi.ac.uk/ena/data/view/",
    "http://arabidopsis.org/servlets/TairObject?accession=",
    # this serves both tair.locus and araport
    "http://bar.utoronto.ca/thalemine/portal.do?externalids=",
    "https://bar.utoronto.ca/thalemine/portal.do?externalids=",
    # serves both pdb and uniprot
    "http://proteins.plus/",
    "https://proteins.plus/",
    # serves multiple clinical trial registries
    "http://trialsearch.who.int/Trial2.aspx?TrialID=",
    "https://trialsearch.who.int/Trial2.aspx?TrialID=",
}
prefix_resource_blacklist = {
    "orphanet": {
        "http://www.orpha.net/ORDO/Orphanet_",  # biocontext is wrong
        "https://www.orpha.net/ORDO/Orphanet_",  # biocontext is wrong
    },
    "wikidata.property": {
        "http://scholia.toolforge.org/",  # duplicated with wikidata
        "https://scholia.toolforge.org/",  # duplicated with wikidata
    },
    "uniprot": {
        "https://www.ncbi.nlm.nih.gov/protein/",  # FIXME not sure how to resolve this
        "http://www.ncbi.nlm.nih.gov/protein/",
    },
    "cl": {
        "https://www.ebi.ac.uk/ols/ontologies/cl/terms?iri=http://purl.obolibrary.org/obo/",
        "http://www.ebi.ac.uk/ols/ontologies/cl/terms?iri=http://purl.obolibrary.org/obo/",
    },
    "uberon": {
        "http://www.ebi.ac.uk/ols/ontologies/cl/terms?iri=http://purl.obolibrary.org/obo/",
        "https://www.ebi.ac.uk/ols/ontologies/cl/terms?iri=http://purl.obolibrary.org/obo/",
    },
    "ncbigene": {
        "https://en.wikipedia.org/wiki/",  # probably from wikigene?
        "http://en.wikipedia.org/wiki/",
    },
    "wbphenotype": {
        "http://www.wormbase.org/get?name=",  # wrong in GO
        "https://www.wormbase.org/get?name=",  # wrong in GO
    },
    "wbls": {
        "http://www.wormbase.org/get?name=",  # wrong in GO
        "https://www.wormbase.org/get?name=",  # wrong in GO
    },
    "uniprot.isoform": {
        "http://www.uniprot.org/uniprot/",  # wrong in miriam
        "https://www.uniprot.org/uniprot/",  # wrong in miriam
        "http://purl.uniprot.org/uniprot/",  # wrong in miriam
        "https://purl.uniprot.org/uniprot/",  # wrong in miriam
    },
}


def _debug_or_raise(msg: str, strict: bool = False) -> None:
    if strict:
        raise ValueError(msg)
    logger.debug(msg)


def _stratify_resources(
    resources: Iterable[Resource],
) -> tuple[list[Resource], list[tuple[Resource, str]]]:
    primary_resources = []
    secondary_resources = []

    # TODO only call it as secondary if it has an overlap with the primary

    for resource in resources:
        primary_prefix = resource.provides or resource.has_canonical or resource.part_of
        if primary_prefix is not None:
            # TODO there's some nuance to the order here, make resource.part_of the last.
            secondary_resources.append((resource, primary_prefix))
        else:
            primary_resources.append(resource)
    return primary_resources, secondary_resources


def _iterate_prefix_prefix(resource: Resource, *extras: str) -> Iterable[str]:
    prefixes_ = [
        resource.prefix,
        *resource.get_synonyms(),
        resource.get_preferred_prefix(),
        *extras,
    ]
    for prefix_ in prefixes_:
        if not prefix_:
            continue
        yield from [
            f"{prefix_}:",
            f"{prefix_.upper()}:",
            f"{prefix_.lower()}:",
        ]


# TODO handle situations where a URI format string is available but
#  it is not directly convertable to URI prefix -> use Bioregistry
#  URL for these (e.g., chemspider, lrg)

# TODO handle when one URI is a subspace of another
#  (e.g., uniprot.isoform and uniprot)


def get_converter(
    resources: list[Resource],
    prefix_priority: Sequence[str] | None = None,
    uri_prefix_priority: Sequence[str] | None = None,
    include_prefixes: bool = False,
    blacklist: Collection[str] | None = None,
    remapping: Mapping[str, str] | None = None,
    rewiring: Mapping[str, str] | None = None,
    enforce_w3c: bool = False,
    include_bioregistry: bool = False,
) -> Converter:
    """Generate a converter from resources."""
    converter = _get_converter(
        resources,
        prefix_priority=prefix_priority,
        uri_prefix_priority=uri_prefix_priority,
        include_prefixes=include_prefixes,
        blacklist=blacklist,
        enforce_w3c=enforce_w3c,
        include_bioregistry=include_bioregistry,
    )
    if remapping:
        converter = curies.remap_curie_prefixes(converter, remapping)
    if rewiring:
        converter = curies.rewire(converter, rewiring)
    if enforce_w3c:
        converter = _w3c_clean_converter(converter)
    return converter


def _w3c_clean_record(record: Record) -> Record:
    record.prefix_synonyms = [s for s in record.prefix_synonyms if NCNAME_RE.match(s)]
    return record


def _w3c_clean_converter(converter: Converter) -> Converter:
    """Remove all non-W3C-compliant records in the converter."""
    return Converter(_w3c_clean_record(record) for record in converter.records)


def _get_converter(
    resources: list[Resource],
    prefix_priority: Sequence[str] | None = None,
    uri_prefix_priority: Sequence[str] | None = None,
    include_prefixes: bool = False,
    blacklist: Collection[str] | None = None,
    enforce_w3c: bool = False,
    include_bioregistry: bool = False,
) -> curies.Converter:
    blacklist = set(blacklist or []).union(prefix_blacklist)
    resources = [r for r in resources if r.prefix not in blacklist]
    converter = curies.Converter()

    primary_resources, secondary_resources = _stratify_resources(resources)

    for resource in primary_resources:
        primary_uri_prefix, secondary_uri_prefixes = _get_uri_prefixes(
            resource,
            uri_prefix_priority,
            enforce_w3c=enforce_w3c,
            include_bioregistry=include_bioregistry,
        )
        if primary_uri_prefix is None:
            continue
        primary_prefix, secondary_prefixes = _get_curie_prefixes(resource, prefix_priority)
        converter.add_prefix(
            primary_prefix,
            primary_uri_prefix,
            secondary_prefixes,
            secondary_uri_prefixes,
            pattern=resource.get_pattern(),
            merge=False,
        )
        if include_prefixes:
            converter.add_uri_prefix_synonym(primary_prefix, f"{primary_prefix}:")
            converter.add_uri_prefix_synonym(primary_prefix, f"{primary_prefix.upper()}:")
            converter.add_uri_prefix_synonym(primary_prefix, f"{primary_prefix.lower()}:")
            for secondary_prefix in secondary_prefixes:
                converter.add_uri_prefix_synonym(primary_prefix, f"{secondary_prefix}:")
                converter.add_uri_prefix_synonym(primary_prefix, f"{secondary_prefix.upper()}:")
                converter.add_uri_prefix_synonym(primary_prefix, f"{secondary_prefix.lower()}:")

    for resource, primary_prefix in secondary_resources:
        secondary_uri_prefix, secondary_uri_prefixes = _get_uri_prefixes(
            resource,
            uri_prefix_priority,
            enforce_w3c=enforce_w3c,
            include_bioregistry=include_bioregistry,
        )
        if secondary_uri_prefix:
            converter.add_uri_prefix_synonym(primary_prefix, secondary_uri_prefix)
            for s in secondary_uri_prefixes:
                converter.add_uri_prefix_synonym(primary_prefix, s)

        secondary_prefix, tertiary_prefixes = _get_curie_prefixes(resource, prefix_priority)
        converter.add_prefix_synonym(primary_prefix, secondary_prefix)
        for s in tertiary_prefixes:
            converter.add_prefix_synonym(primary_prefix, s)

        if include_prefixes:
            if include_prefixes:
                converter.add_uri_prefix_synonym(primary_prefix, f"{secondary_prefix}:")
                converter.add_uri_prefix_synonym(primary_prefix, f"{secondary_prefix.upper()}:")
                converter.add_uri_prefix_synonym(primary_prefix, f"{secondary_prefix.lower()}:")
                for tertiary_prefix in tertiary_prefixes:
                    converter.add_uri_prefix_synonym(primary_prefix, f"{tertiary_prefix}:")
                    converter.add_uri_prefix_synonym(primary_prefix, f"{tertiary_prefix.upper()}:")
                    converter.add_uri_prefix_synonym(primary_prefix, f"{tertiary_prefix.lower()}:")

    return converter


def _get_curie_prefixes(
    resource: Resource, priority: Sequence[str] | None = None
) -> tuple[str, set[str]]:
    primary = resource.get_priority_prefix(priority)
    if primary in {"geo", "geogeo", "BOOTSTREP", "gramene.growthstage"}:
        return primary, set()

    # TODO upstream synonym getting functionality
    rest = resource.get_synonyms()
    rest.add(resource.prefix)
    if pp := resource.get_preferred_prefix():
        rest.add(pp)
    rest.update({r.lower() for r in rest})
    rest.update({r.upper() for r in rest})
    if primary in rest:
        rest.remove(primary)
    return primary, rest


@overload
def _get_uri_prefixes(
    resource: Resource,
    priority: Sequence[str] | None,
    enforce_w3c: bool,
    include_bioregistry: Literal[True] = ...,
) -> tuple[str, set[str]]: ...


@overload
def _get_uri_prefixes(
    resource: Resource,
    priority: Sequence[str] | None,
    enforce_w3c: bool,
    include_bioregistry: Literal[False] = ...,
) -> tuple[str | None, set[str]]: ...


def _get_uri_prefixes(
    resource: Resource,
    priority: Sequence[str] | None,
    enforce_w3c: bool,
    include_bioregistry: bool = False,
) -> tuple[str | None, set[str]] | tuple[str, set[str]]:
    primary = resource.get_uri_prefix(priority=priority, include_bioregistry=include_bioregistry)
    rest = (
        resource.get_uri_prefixes(enforce_w3c=enforce_w3c)
        - {primary}
        - prefix_resource_blacklist.get(resource.prefix, set())
        - uri_prefix_blacklist
    )
    return primary, rest
