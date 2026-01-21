"""Generating records for :mod:`curies`."""

from __future__ import annotations

import itertools as itt
import logging
from collections import defaultdict
from collections.abc import Collection, Iterable, Mapping, Sequence
from typing import cast

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
    strict: bool = False,
    blacklist: Collection[str] | None = None,
    remapping: Mapping[str, str] | None = None,
    rewiring: Mapping[str, str] | None = None,
    enforce_w3c: bool = False,
    use_new_implementation: bool = True,
) -> Converter:
    """Generate a converter from resources."""
    if use_new_implementation:
        converter = _get_converter(
            resources,
            prefix_priority=prefix_priority,
            uri_prefix_priority=uri_prefix_priority,
            include_prefixes=include_prefixes,
            blacklist=blacklist,
            enforce_w3c=enforce_w3c,
        )
    else:
        converter = curies.Converter(
            _get_records(
                resources,
                prefix_priority=prefix_priority,
                uri_prefix_priority=uri_prefix_priority,
                include_prefixes=include_prefixes,
                strict=strict,
                blacklist=blacklist,
                enforce_w3c=enforce_w3c,
            )
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
) -> curies.Converter:
    blacklist = set(blacklist or []).union(prefix_blacklist)
    resources = [r for r in resources if r.prefix not in blacklist]
    converter = curies.Converter()

    primary_resources, secondary_resources = _stratify_resources(resources)

    for resource in primary_resources:
        primary_uri_prefix, secondary_uri_prefixes = _get_uri_prefixes(
            resource, uri_prefix_priority, enforce_w3c=enforce_w3c
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
            resource, uri_prefix_priority, enforce_w3c=enforce_w3c
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


def _get_uri_prefixes(
    resource: Resource, priority: Sequence[str] | None, enforce_w3c: bool
) -> tuple[str | None, set[str]]:
    primary = resource.get_uri_prefix(priority=priority)
    rest = (
        resource.get_uri_prefixes(enforce_w3c=enforce_w3c)
        - {primary}
        - prefix_resource_blacklist.get(resource.prefix, set())
        - uri_prefix_blacklist
    )
    return primary, rest


def _get_records(
    resources: list[Resource],
    prefix_priority: Sequence[str] | None = None,
    uri_prefix_priority: Sequence[str] | None = None,
    include_prefixes: bool = False,
    strict: bool = False,
    blacklist: Collection[str] | None = None,
    enforce_w3c: bool = False,
) -> list[curies.Record]:
    """Generate records from resources."""
    blacklist = set(blacklist or []).union(prefix_blacklist)
    resource_dict: Mapping[str, Resource] = {
        resource.prefix: resource
        for resource in resources
        if resource.get_uri_prefix() and resource.prefix not in blacklist
    }
    primary_uri_prefixes: dict[str, str] = {
        resource.prefix: cast(str, resource.get_uri_prefix(priority=uri_prefix_priority))
        for resource in resource_dict.values()
    }
    primary_prefixes: dict[str, str] = {
        resource.prefix: resource.get_priority_prefix(priority=prefix_priority)
        for resource in resource_dict.values()
    }
    pattern_map = {
        prefix: pattern
        for prefix in primary_prefixes
        if (pattern := resource_dict[prefix].get_pattern()) is not None
    }
    secondary_prefixes: defaultdict[str, set[str]] = defaultdict(set)
    secondary_uri_prefixes: defaultdict[str, set[str]] = defaultdict(set)

    #: A mapping from URI prefixes (both primary and secondary) appearing
    #: in all records to bioregistry prefixes
    reverse_uri_prefix_lookup: dict[str, str] = {
        "http://purl.obolibrary.org/obo/": "obo",
        "https://purl.obolibrary.org/obo/": "obo",
    }
    #: A mapping from prefixes (both primary and secondary) appearing
    #: in all records to bioregistry prefixes
    reverse_prefix_lookup: dict[str, str] = {}

    def _add_primary_uri_prefix(prefix: str) -> str | None:
        primary_uri_prefix = primary_uri_prefixes[prefix]
        if primary_uri_prefix in reverse_uri_prefix_lookup:
            logger.debug(
                "duplicate primary URI prefix: %s for %s that already appeared in %s",
                primary_uri_prefix,
                prefix,
                reverse_uri_prefix_lookup[primary_uri_prefix],
            )
            # primary_uri_prefix = f"https://bioregistry.io/{resource.prefix}:"
            return None
        reverse_uri_prefix_lookup[primary_uri_prefix] = prefix
        return primary_uri_prefix

    def _add_primary_prefix(prefix: str) -> str | None:
        primary_prefix = primary_prefixes[prefix]
        if primary_prefix in reverse_prefix_lookup:
            logger.debug(
                "duplicate primary prefix: %s for %s that already appeared in %s",
                primary_prefix,
                prefix,
                reverse_prefix_lookup[primary_prefix],
            )
            return None
        reverse_prefix_lookup[primary_prefix] = prefix
        if primary_prefix not in {"geo", "geogeo"}:
            # FIXME this weird hack is not sustainable
            secondary_prefixes[primary_prefix].add(primary_prefix.upper())
        secondary_prefixes[primary_prefix].add(primary_prefix.lower())
        return primary_prefix

    def _add_synonym(*, synonym: str, prefix: str) -> None:
        if synonym in reverse_prefix_lookup:
            if reverse_prefix_lookup[synonym] == prefix:
                return
            msg = f"duplicate prefix in {reverse_prefix_lookup[synonym]} and {prefix}: {synonym}"
            _debug_or_raise(msg, strict=strict)
            return
        reverse_prefix_lookup[synonym] = prefix
        secondary_prefixes[prefix].add(synonym)
        secondary_prefixes[prefix].add(synonym.lower())
        secondary_prefixes[prefix].add(synonym.upper())

    def _add_uri_synonym(*, uri_prefix: str, prefix: str) -> None:
        if uri_prefix in prefix_resource_blacklist.get(prefix, set()):
            return
        elif uri_prefix in uri_prefix_blacklist:
            return
        elif uri_prefix in reverse_uri_prefix_lookup:
            if prefix == reverse_uri_prefix_lookup[uri_prefix]:
                return  # this is already in
            msg = f"duplicate URI prefix in {reverse_uri_prefix_lookup[uri_prefix]} and {prefix}: {uri_prefix}"
            _debug_or_raise(msg, strict=strict)
            return
        else:
            reverse_uri_prefix_lookup[uri_prefix] = prefix
            secondary_uri_prefixes[prefix].add(uri_prefix)

    def _add_prefix_prefixes(
        primary_prefix: str, resource: Resource, target_prefix: str | None = None
    ) -> None:
        if target_prefix is None:
            target_prefix = resource.prefix
        for prefix_prefix in _iterate_prefix_prefix(resource, primary_prefix):
            if prefix_prefix in reverse_uri_prefix_lookup:
                if reverse_uri_prefix_lookup[prefix_prefix] == resource.prefix:
                    continue
                msg = (
                    f"duplicate prefix prefix in {reverse_uri_prefix_lookup[prefix_prefix]} "
                    f"and {resource.prefix}: {prefix_prefix}"
                )
                _debug_or_raise(msg, strict=strict)
                continue
            reverse_uri_prefix_lookup[prefix_prefix] = target_prefix
            secondary_uri_prefixes[target_prefix].add(prefix_prefix)

    primary_resources, secondary_resources = _stratify_resources(resource_dict.values())
    for resource in itt.chain(primary_resources):
        primary_uri_prefix = _add_primary_uri_prefix(resource.prefix)
        if primary_uri_prefix is None:
            continue
        primary_prefix = _add_primary_prefix(resource.prefix)
        if primary_prefix is None:
            continue
        for synonym in resource.get_synonyms():
            _add_synonym(synonym=synonym, prefix=resource.prefix)
        for uri_prefix in resource.get_uri_prefixes(enforce_w3c=enforce_w3c):
            _add_uri_synonym(uri_prefix=uri_prefix, prefix=resource.prefix)
        if include_prefixes:
            _add_prefix_prefixes(primary_prefix=primary_prefix, resource=resource)

    for resource, _ in secondary_resources:
        provides = resource.provides
        canonical = resource.has_canonical
        has_part = resource.part_of
        if provides is not None or canonical is not None:
            prefix = cast(str, provides or canonical)
            # remove from cache so it doesn't get its own entry
            primary_prefix = primary_prefixes.pop(resource.prefix)
            if primary_prefix not in reverse_prefix_lookup:
                reverse_prefix_lookup[primary_prefix] = prefix
                secondary_prefixes[prefix].add(primary_prefix)
            primary_uri_prefix = primary_uri_prefixes.pop(resource.prefix)
            if primary_uri_prefix not in reverse_uri_prefix_lookup:
                reverse_uri_prefix_lookup[primary_uri_prefix] = prefix
                secondary_uri_prefixes[prefix].add(primary_uri_prefix)
            _add_synonym(synonym=resource.prefix, prefix=prefix)
            for synonym in resource.get_synonyms():
                _add_synonym(synonym=synonym, prefix=prefix)
            for uri_prefix in resource.get_uri_prefixes(enforce_w3c=enforce_w3c):
                _add_uri_synonym(uri_prefix=uri_prefix, prefix=prefix)
            if include_prefixes:
                _add_prefix_prefixes(
                    primary_prefix=primary_prefix, resource=resource, target_prefix=prefix
                )
        elif has_part:
            uri_prefixes = {
                p
                for p in resource.get_uri_prefixes(enforce_w3c=enforce_w3c)
                if p not in prefix_resource_blacklist.get(resource.prefix, set())
            }
            _duplicats = [
                uri_prefix for uri_prefix in uri_prefixes if uri_prefix in reverse_uri_prefix_lookup
            ]
            if _duplicats and has_part in primary_uri_prefixes:
                del primary_prefixes[resource.prefix]
                del primary_uri_prefixes[resource.prefix]
                _add_synonym(synonym=resource.prefix, prefix=has_part)
                for synonym in resource.get_synonyms():
                    _add_synonym(synonym=synonym, prefix=has_part)
                for uri_prefix in uri_prefixes:
                    _add_uri_synonym(uri_prefix=uri_prefix, prefix=has_part)
                if include_prefixes:
                    _add_prefix_prefixes(
                        primary_prefix=primary_prefixes[has_part],
                        resource=resource,
                        target_prefix=has_part,
                    )
            else:
                primary_uri_prefix = _add_primary_uri_prefix(resource.prefix)
                if primary_uri_prefix is None:
                    continue
                primary_prefix = _add_primary_prefix(resource.prefix)
                if primary_prefix is None:
                    continue
                for synonym in resource.get_synonyms():
                    _add_synonym(synonym=synonym, prefix=resource.prefix)
                for uri_prefix in resource.get_uri_prefixes(enforce_w3c=enforce_w3c):
                    _add_uri_synonym(uri_prefix=uri_prefix, prefix=resource.prefix)
                if include_prefixes:
                    _add_prefix_prefixes(primary_prefix=primary_prefix, resource=resource)

        else:
            raise RuntimeError

    records: dict[str, curies.Record] = {}
    for prefix, primary_prefix in primary_prefixes.items():
        primary_uri_prefix = primary_uri_prefixes[prefix]
        if not primary_prefix or not primary_uri_prefix:
            continue
        records[prefix] = curies.Record(
            prefix=primary_prefix,
            prefix_synonyms=sorted(secondary_prefixes[prefix].union({prefix}) - {primary_prefix}),
            uri_prefix=primary_uri_prefix,
            uri_prefix_synonyms=sorted(secondary_uri_prefixes[prefix] - {primary_uri_prefix}),
            pattern=pattern_map.get(prefix),
        )

    return [record for _, record in sorted(records.items())]
