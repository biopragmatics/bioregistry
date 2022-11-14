# -*- coding: utf-8 -*-

"""A class-based client to a metaregistry."""

import logging
import typing
from collections import Counter, defaultdict
from functools import lru_cache
from pathlib import Path
from typing import (
    Any,
    Callable,
    Dict,
    Iterable,
    List,
    Mapping,
    Optional,
    Sequence,
    Set,
    Tuple,
    Union,
    cast,
)

import curies

from .constants import (
    BIOREGISTRY_REMOTE_URL,
    EXTRAS,
    HEALTH_BASE,
    IDENTIFIERS_ORG_URL_PREFIX,
    LINK_PRIORITY,
    SHIELDS_BASE,
)
from .license_standardizer import standardize_license
from .schema import (
    Attributable,
    Collection,
    Context,
    Registry,
    Resource,
    sanitize_model,
)
from .schema_utils import (
    _read_metaregistry,
    _registry_from_path,
    read_collections,
    read_contexts,
    read_metaregistry,
    read_mismatches,
    read_registry,
    write_registry,
)
from .utils import NormDict, _norm, curie_to_str

__all__ = [
    "Manager",
    "manager",
]

logger = logging.getLogger(__name__)


def _synonym_to_canonical(registry: Mapping[str, Resource]) -> NormDict:
    """Return a mapping from several variants of each synonym to the canonical namespace."""
    norm_synonym_to_key = NormDict()

    for identifier, resource in registry.items():
        norm_synonym_to_key[identifier] = identifier
        for synonym in resource.synonyms or []:
            norm_synonym_to_key[synonym] = identifier

        for metaprefix in ("miriam", "ols", "obofoundry", "go"):
            external = resource.get_external(metaprefix)
            if external is None:
                continue
            external_prefix = external.get("prefix")
            if external_prefix is None:
                continue
            if external_prefix not in norm_synonym_to_key:
                logger.debug(f"[{identifier}] missing potential synonym: {external_prefix}")

    return norm_synonym_to_key


class Manager:
    """A manager for functionality related to a metaregistry."""

    registry: Dict[str, Resource]
    metaregistry: Dict[str, Registry]
    collections: Dict[str, Collection]
    contexts: Dict[str, Context]
    mismatches: Mapping[str, Mapping[str, str]]

    def __init__(
        self,
        registry: Union[None, str, Path, Mapping[str, Resource]] = None,
        metaregistry: Union[None, str, Path, Mapping[str, Registry]] = None,
        collections: Optional[Mapping[str, Collection]] = None,
        contexts: Optional[Mapping[str, Context]] = None,
        mismatches: Optional[Mapping[str, Mapping[str, str]]] = None,
    ):
        """Instantiate a registry manager.

        :param registry: A custom registry. If none given, defaults to the Bioregistry.
        :param metaregistry: A custom metaregistry. If none, defaults to the Bioregistry's metaregistry.
        :param collections: A custom collections dictionary. If none, defaults to the Bioregistry's collections.
        :param contexts: A custom contexts dictionary. If none, defaults to the Bioregistry's contexts.
        :param mismatches: A custom mismatches dictionary. If none, defaults to the Bioregistry's mismatches.
        """
        if registry is None:
            self.registry = dict(read_registry())
        elif isinstance(registry, (str, Path)):
            self.registry = dict(_registry_from_path(registry))
        else:
            self.registry = dict(registry)
        self.synonyms = _synonym_to_canonical(self.registry)

        if metaregistry is None:
            self.metaregistry = dict(read_metaregistry())
        elif isinstance(metaregistry, (str, Path)):
            self.metaregistry = dict(_read_metaregistry(metaregistry))
        else:
            self.metaregistry = dict(metaregistry)
        self.collections = dict(read_collections() if collections is None else collections)
        self.contexts = dict(read_contexts() if contexts is None else contexts)
        self.mismatches = dict(read_mismatches() if mismatches is None else mismatches)

        canonical_for = defaultdict(list)
        provided_by = defaultdict(list)
        has_parts = defaultdict(list)
        for prefix, resource in self.registry.items():
            if resource.has_canonical:
                canonical_for[resource.has_canonical].append(prefix)
            if resource.provides:
                provided_by[resource.provides].append(prefix)
            if resource.part_of:
                has_parts[resource.part_of].append(prefix)
        self.canonical_for = dict(canonical_for)
        self.provided_by = dict(provided_by)
        self.has_parts = dict(has_parts)

    def write_registry(self):
        """Write the registry."""
        write_registry(self.registry)

    def get_registry(self, metaprefix: str) -> Optional[Registry]:
        """Get the metaregistry entry for the given prefix."""
        return self.metaregistry.get(metaprefix)

    def get_registry_name(self, metaprefix: str) -> Optional[str]:
        """Get the registry name."""
        registry = self.get_registry(metaprefix)
        if registry is None:
            return None
        return registry.name

    def get_registry_homepage(self, metaprefix: str) -> Optional[str]:
        """Get the registry homepage."""
        registry = self.get_registry(metaprefix)
        if registry is None:
            return None
        return registry.homepage

    def get_registry_description(self, metaprefix: str) -> Optional[str]:
        """Get the registry description."""
        registry = self.get_registry(metaprefix)
        if registry is None:
            return None
        return registry.description

    def get_registry_provider_uri_format(self, metaprefix: str, prefix: str) -> Optional[str]:
        """Get the URL for the resource inside registry, if available."""
        entry = self.get_registry(metaprefix)
        if entry is None:
            return None
        return entry.get_provider_uri_format(prefix)

    def normalize_prefix(self, prefix: str) -> Optional[str]:
        """Get the normalized prefix, or return None if not registered.

        :param prefix: The prefix to normalize, which could come from Bioregistry,
            OBO Foundry, OLS, or any of the curated synonyms in the Bioregistry
        :returns: The canonical Bioregistry prefix, it could be looked up. This
            will usually take precedence: MIRIAM, OBO Foundry / OLS, Custom except
            in a few cases, such as NCBITaxon.
        """
        return self.synonyms.get(prefix)

    def get_resource(self, prefix: str) -> Optional[Resource]:
        """Get the Bioregistry entry for the given prefix.

        :param prefix: The prefix to look up, which is normalized with :func:`normalize_prefix`
            before lookup in the Bioregistry
        :returns: The Bioregistry entry dictionary, which includes several keys cross-referencing
            other registries when available.
        """
        norm_prefix = self.normalize_prefix(prefix)
        if norm_prefix is None:
            return None
        return self.registry.get(norm_prefix)

    def parse_curie(self, curie: str, sep: str = ":") -> Union[Tuple[str, str], Tuple[None, None]]:
        """Parse a CURIE and normalize its prefix and identifier."""
        try:
            prefix, identifier = curie.split(sep, 1)
        except ValueError:
            return None, None
        return self.normalize_parsed_curie(prefix, identifier)

    def normalize_curie(self, curie: str, sep: str = ":") -> Optional[str]:
        """Normalize the prefix and identifier in the CURIE."""
        prefix, identifier = self.parse_curie(curie, sep=sep)
        if prefix is None or identifier is None:
            return None
        return curie_to_str(prefix, identifier)

    def normalize_parsed_curie(
        self, prefix: str, identifier: str
    ) -> Union[Tuple[str, str], Tuple[None, None]]:
        """Normalize a prefix/identifier pair.

        :param prefix: The prefix in the CURIE
        :param identifier: The identifier in the CURIE
        :return: A normalized prefix/identifier pair, conforming to Bioregistry standards. This means no redundant
            prefixes or bananas, all lowercase.
        """
        norm_prefix = self.normalize_prefix(prefix)
        if not norm_prefix:
            return None, None
        resource = self.registry[norm_prefix]
        norm_identifier = resource.standardize_identifier(identifier)
        return norm_prefix, norm_identifier

    @lru_cache(maxsize=None)  # noqa:B019
    def get_registry_map(self, metaprefix: str) -> Dict[str, str]:
        """Get a mapping from the Bioregistry prefixes to prefixes in another registry."""
        return dict(self._iter_registry_map(metaprefix))

    @lru_cache(maxsize=None)  # noqa:B019
    def get_registry_invmap(self, metaprefix: str, normalize: bool = False) -> Dict[str, str]:
        """Get a mapping from prefixes in another registry to Bioregistry prefixes.

        :param metaprefix: Which external registry should be used?
        :param normalize: Should the external prefixes be normalized?
        :returns: A mapping of external prefixes to bioregistry prefies

        >>> from bioregistry import manager
        >>> obofoundry_to_bioregistry = manager.get_registry_invmap("obofoundry", normalize=True)
        >>> obofoundry_to_bioregistry["go"]
        'go'
        >>> obofoundry_to_bioregistry["geo"]
        'geogeo'
        """
        if normalize:
            return {
                _norm(external_prefix): prefix
                for prefix, external_prefix in self._iter_registry_map(metaprefix)
            }
        return {
            external_prefix: prefix
            for prefix, external_prefix in self._iter_registry_map(metaprefix)
        }

    def _iter_registry_map(self, metaprefix: str) -> Iterable[Tuple[str, str]]:
        for prefix, resource in self.registry.items():
            mapped_prefix = resource.get_mapped_prefix(metaprefix)
            if mapped_prefix is not None:
                yield prefix, mapped_prefix

    def get_mapped_prefix(self, prefix: str, metaprefix: str) -> Optional[str]:
        """Get the prefix mapped into another registry."""
        resource = self.get_resource(prefix)
        if resource is None:
            return None
        return resource.get_mapped_prefix(metaprefix)

    def get_external(self, prefix: str, metaprefix: str) -> Mapping[str, Any]:
        """Get the external data for the entry."""
        entry = self.get_resource(prefix)
        if entry is None:
            return {}
        return entry.get_external(metaprefix)

    def get_versions(self) -> Mapping[str, str]:
        """Get a map of prefixes to versions."""
        rv = {}
        for prefix, resource in self.registry.items():
            version = resource.get_version()
            if version is not None:
                rv[prefix] = version
        return rv

    def get_uri_format(self, prefix, priority: Optional[Sequence[str]] = None) -> Optional[str]:
        """Get the URI format string for the given prefix, if it's available."""
        entry = self.get_resource(prefix)
        if entry is None:
            return None
        return entry.get_uri_format(priority=priority)

    def get_uri_prefix(self, prefix, priority: Optional[Sequence[str]] = None) -> Optional[str]:
        """Get a well-formed URI prefix, if available."""
        entry = self.get_resource(prefix)
        if entry is None:
            return None
        return entry.get_uri_prefix(priority=priority)

    def get_name(self, prefix: str) -> Optional[str]:
        """Get the name for the given prefix, it it's available."""
        entry = self.get_resource(prefix)
        if entry is None:
            return None
        return entry.get_name()

    def get_description(self, prefix: str, *, use_markdown: bool = False) -> Optional[str]:
        """Get the description for the given prefix, it it's available."""
        entry = self.get_resource(prefix)
        if entry is None:
            return None
        return entry.get_description(use_markdown=use_markdown)

    def get_homepage(self, prefix: str) -> Optional[str]:
        """Get the description for the given prefix, it it's available."""
        entry = self.get_resource(prefix)
        if entry is None:
            return None
        return entry.get_homepage()

    def get_preferred_prefix(self, prefix: str) -> Optional[str]:
        """Get the preferred prefix (e.g., with stylization) if it exists."""
        entry = self.get_resource(prefix)
        if entry is None:
            return None
        return entry.get_preferred_prefix()

    def get_pattern(self, prefix: str) -> Optional[str]:
        """Get the pattern for the given prefix, if it's available."""
        entry = self.get_resource(prefix)
        if entry is None:
            return None
        return entry.get_pattern()

    def get_synonyms(self, prefix: str) -> Optional[Set[str]]:
        """Get the synonyms for a given prefix, if available."""
        entry = self.get_resource(prefix)
        if entry is None:
            return None
        return entry.get_synonyms()

    def get_example(self, prefix: str) -> Optional[str]:
        """Get an example identifier, if it's available."""
        entry = self.get_resource(prefix)
        if entry is None:
            return None
        return entry.get_example()

    def has_no_terms(self, prefix: str) -> bool:
        """Get if the entry has been annotated to not have own terms."""
        entry = self.get_resource(prefix)
        if entry is None or entry.no_own_terms is None:
            return False
        return entry.no_own_terms

    def is_deprecated(self, prefix: str) -> bool:
        """Return if the given prefix corresponds to a deprecated resource."""
        entry = self.get_resource(prefix)
        if entry is None:
            return False
        return entry.is_deprecated()

    def get_pattern_map(
        self,
        *,
        prefix_priority: Optional[Sequence[str]] = None,
        include_synonyms: bool = False,
        remapping: Optional[Mapping[str, str]] = None,
        blacklist: Optional[typing.Collection[str]] = None,
    ) -> Mapping[str, str]:
        """Get a mapping from prefixes to their regular expression patterns.

        :param prefix_priority:
            The order of metaprefixes OR "preferred" for choosing a primary prefix
            OR "default" for Bioregistry prefixes
        :param include_synonyms: Should synonyms of each prefix also be included as additional prefixes, but with
            the same URI prefix?
        :param remapping: A mapping from prefixes to preferred prefixes.
        :param blacklist: Prefixes to skip
        :return: A mapping from prefixes to regular expression pattern strings.
        """
        it = self._iter_pattern_map(
            include_synonyms=include_synonyms, prefix_priority=prefix_priority, blacklist=blacklist
        )
        if not remapping:
            return dict(it)
        return {remapping.get(prefix, prefix): uri_prefix for prefix, uri_prefix in it}

    def _iter_pattern_map(
        self,
        *,
        prefix_priority: Optional[Sequence[str]] = None,
        include_synonyms: bool = False,
        blacklist: Optional[typing.Collection[str]] = None,
    ) -> Iterable[Tuple[str, str]]:
        blacklist = set(blacklist or [])
        for resource in self.registry.values():
            if resource.prefix in blacklist:
                continue
            pattern = resource.get_pattern()
            if pattern is None:
                continue
            prefix = resource.get_priority_prefix(priority=prefix_priority)
            yield prefix, pattern
            if include_synonyms:
                for synonym in resource.get_synonyms():
                    yield synonym, pattern

    def get_converter(self, **kwargs) -> curies.Converter:
        """Get a converter from this manager."""
        return curies.Converter(records=self.get_curies_records(**kwargs))

    def get_curies_records(
        self,
        prefix_priority: Optional[Sequence[str]] = None,
        uri_prefix_priority: Optional[Sequence[str]] = None,
        include_prefixes: bool = False,
        strict: bool = False,
        remapping: Optional[Mapping[str, str]] = None,
        blacklist: Optional[typing.Collection[str]] = None,
    ) -> List[curies.Record]:
        """Get a list of records for all resources in this manager.

        :param prefix_priority:
            The order of metaprefixes OR "preferred" for choosing a primary prefix
            OR "default" for Bioregistry prefixes
        :param uri_prefix_priority:
            The order of metaprefixes for choosing the primary URI prefix OR
            "default" for Bioregistry prefixes
        :param include_prefixes: Should prefixes be included with colon delimiters?
            Setting this to true makes an "omni"-reverse prefix map that can be
            used to parse both URIs and CURIEs
        :param strict:
            If true, errors on URI prefix collisions. If false, sends logging
            and skips them.
        :param remapping: A mapping from bioregistry prefixes to preferred prefixes.
        :param blacklist:
            A collection of prefixes to skip

        :returns: A list of records for :class:`curies.Converter`
        """
        from .record_accumulator import get_records

        resources = [
            resource for _, resource in sorted(self.registry.items()) if resource.get_uri_prefix()
        ]
        return get_records(
            resources,
            prefix_priority=prefix_priority,
            uri_prefix_priority=uri_prefix_priority,
            include_prefixes=include_prefixes,
            strict=strict,
            blacklist=blacklist,
            remapping=remapping,
        )

    def get_reverse_prefix_map(
        self, include_prefixes: bool = False, strict: bool = False
    ) -> Mapping[str, str]:
        """Get a reverse prefix map, pointing to canonical prefixes."""
        from .record_accumulator import _iterate_prefix_prefix

        rv: Dict[str, str] = {
            "http://purl.obolibrary.org/obo/": "obo",
            "https://purl.obolibrary.org/obo/": "obo",
        }
        for record in self.get_curies_records(include_prefixes=include_prefixes, strict=strict):
            rv[record.uri_prefix] = record.prefix
            for uri_prefix in record.uri_prefix_synonyms:
                if uri_prefix not in rv:
                    rv[uri_prefix] = record.prefix
                elif rv[uri_prefix] == record.prefix:
                    # no big deal, it's a trivial duplicate
                    # FIXME this shouldn't happen, though
                    pass
                else:
                    logger.warning(
                        f"non-trivial duplicate secondary URI prefix {uri_prefix} in {record.prefix} that "
                        f"already appeared in {rv[uri_prefix]}"
                    )
                for synonym in (record.prefix, *record.prefix_synonyms):
                    rv[f"{synonym}:"] = record.prefix

        for resource in self.registry.values():
            if not resource.get_uri_prefix():
                for pp in _iterate_prefix_prefix(resource):
                    rv[pp] = resource.prefix

        return rv

    def get_prefix_map(
        self,
        *,
        uri_prefix_priority: Optional[Sequence[str]] = None,
        prefix_priority: Optional[Sequence[str]] = None,
        include_synonyms: bool = False,
        remapping: Optional[Mapping[str, str]] = None,
        blacklist: Optional[typing.Collection[str]] = None,
    ) -> Mapping[str, str]:
        """Get a mapping from Bioregistry prefixes to their URI prefixes .

        :param prefix_priority:
            The order of metaprefixes OR "preferred" for choosing a primary prefix
            OR "default" for Bioregistry prefixes
        :param uri_prefix_priority:
            The order of metaprefixes for choosing the primary URI prefix OR
            "default" for Bioregistry prefixes
        :param include_synonyms: Should synonyms of each prefix also be included as additional prefixes, but with
            the same URI prefix?
        :param remapping: A mapping from Bioregistry prefixes to preferred prefixes.
        :param blacklist: Prefixes to skip
        :return: A mapping from prefixes to URI prefixes.
        """
        records = self.get_curies_records(
            prefix_priority=prefix_priority,
            uri_prefix_priority=uri_prefix_priority,
            remapping=remapping,
            blacklist=blacklist,
        )
        rv = {}
        for record in records:
            rv[record.prefix] = record.uri_prefix
            if include_synonyms:
                for prefix in record.prefix_synonyms:
                    rv[prefix] = record.uri_prefix
        return rv

    def get_curie_pattern(self, prefix: str, use_preferred: bool = False) -> Optional[str]:
        r"""Get the CURIE pattern for this resource.

        :param prefix: The prefix to look up
        :param use_preferred: Should the preferred prefix be used instead
            of the Bioregistry prefix (if it exists)?
        :return: The regular expression pattern to match CURIEs against

        >>> from bioregistry import manager
        >>> manager.get_curie_pattern("go")
        '^go:\\d{7}$'
        >>> manager.get_curie_pattern("go", use_preferred=True)
        '^GO:\\d{7}$'
        >>> manager.get_curie_pattern("kegg.compound")
        '^kegg\\.compound:C\\d+$'
        >>> manager.get_curie_pattern("KEGG.COMPOUND")
        '^kegg\\.compound:C\\d+$'
        """
        resource = self.get_resource(prefix)
        if resource is None:
            return None
        pattern = resource.get_pattern()
        if pattern is None:
            return None
        p = resource.get_preferred_prefix() or resource.prefix if use_preferred else resource.prefix
        p = p.replace(".", "\\.")
        return f"^{p}:{pattern.lstrip('^')}"

    def rasterize(self):
        """Build a dictionary representing the fully constituted registry."""
        return {
            prefix: sanitize_model(resource)
            for prefix, resource in self._rasterized_registry().items()
        }

    def _rasterized_registry(self) -> Mapping[str, Resource]:
        return {
            prefix: self.rasterized_resource(prefix, resource)
            for prefix, resource in self.registry.items()
        }

    def rasterized_resource(self, prefix: str, resource: Resource) -> Resource:
        """Rasterize a resource."""
        return Resource(
            prefix=resource.prefix,
            preferred_prefix=resource.get_preferred_prefix() or prefix,
            name=resource.get_name(),
            description=resource.get_description(),
            pattern=resource.get_pattern(),
            homepage=resource.get_homepage(),
            license=resource.get_license(),
            version=resource.get_version(),
            synonyms=resource.get_synonyms(),
            repository=resource.get_repository(),
            # Downloads
            download_obo=resource.get_download_obo(),
            download_json=resource.get_download_obograph(),
            download_owl=resource.get_download_owl(),
            download_rdf=resource.get_download_rdf(),
            # Registry properties
            example=resource.get_example(),
            example_extras=resource.example_extras,
            example_decoys=resource.example_decoys,
            uri_format=resource.get_uri_format(),
            providers=resource.get_extra_providers(),
            # Comments
            comment=resource.comment,
            references=resource.references,
            publications=resource.get_publications(),
            # MIRIAM compatibility
            banana=resource.get_banana(),
            banana_peel=resource.banana_peel,
            namespace_in_lui=resource.get_namespace_in_lui(),
            # Provenance
            contact=resource.get_contact(),
            contributor=resource.contributor,
            contributor_extras=resource.contributor_extras,
            reviewer=resource.reviewer,
            twitter=resource.get_twitter(),
            github_request_issue=resource.github_request_issue,
            # Ontology Relations
            part_of=resource.part_of,
            provides=resource.provides,
            has_canonical=resource.has_canonical,
            appears_in=self.get_appears_in(prefix),
            depends_on=self.get_depends_on(prefix),
            mappings=resource.get_mappings(),
            # Ontology Properties
            deprecated=resource.is_deprecated(),
            no_own_terms=resource.no_own_terms,
            proprietary=resource.proprietary,
        )

    def get_license_conflicts(self):
        """Get license conflicts."""
        conflicts = []
        for prefix, entry in self.registry.items():
            override = entry.license
            obo_license = entry.get_external("obofoundry").get("license")
            ols_license = entry.get_external("ols").get("license")
            if 2 > sum(license_ is not None for license_ in (override, obo_license, ols_license)):
                continue  # can't be a conflict if all none or only 1 is available
            obo_norm = standardize_license(obo_license)
            ols_norm = standardize_license(ols_license)
            first, *rest = [
                norm_license
                for norm_license in (override, obo_norm, ols_norm)
                if norm_license is not None
            ]
            if any(first != element for element in rest):
                conflicts.append((prefix, override, obo_license, ols_license))
        return conflicts

    def get_appears_in(self, prefix: str) -> Optional[List[str]]:
        """Return a list of resources that this resources (has been annotated to) depends on.

        This is complementary to :func:`get_depends_on`.

        :param prefix: The prefix to look up
        :returns: The list of resources this prefix has been annotated to appear in. This
            list could be incomplete, since curation of these fields can easily get out
            of sync with curation of the resource itself. However, false positives should
            be pretty rare.
        """
        resource = self.get_resource(prefix)
        if resource is None:
            return None
        rv = list(resource.appears_in or [])
        rv.extend(self._get_obo_list(prefix=prefix, resource=resource, key="appears_in"))
        return sorted(set(rv))

    def get_depends_on(self, prefix: str) -> Optional[List[str]]:
        """Return a list of resources that this resources (has been annotated to) depends on.

        This is complementary to :func:`get_appears_in`.

        :param prefix: The prefix to look up
        :returns: The list of resources this prefix has been annotated to depend on. This
            list could be incomplete, since curation of these fields can easily get out
            of sync with curation of the resource itself. However, false positives should
            be pretty rare.

        >>> from bioregistry import manager
        >>> assert "bfo" in manager.get_depends_on("foodon")
        """
        resource = self.get_resource(prefix)
        if resource is None:
            return None
        rv = list(resource.depends_on or [])
        rv.extend(self._get_obo_list(prefix=prefix, resource=resource, key="depends_on"))
        return sorted(set(rv))

    def _get_obo_list(self, *, prefix: str, resource: Resource, key: str) -> List[str]:
        rv = []
        for obo_prefix in resource.get_external("obofoundry").get(key, []):
            canonical_prefix = self.lookup_from("obofoundry", obo_prefix, normalize=True)
            if canonical_prefix is None:
                logger.warning("[%s] could not map OBO %s: %s", prefix, key, obo_prefix)
            else:
                rv.append(canonical_prefix)
        return rv

    def lookup_from(
        self, metaprefix: str, metaidentifier: str, normalize: bool = False
    ) -> Optional[str]:
        """Get the bioregistry prefix from an external prefix.

        :param metaprefix: The key for the external registry
        :param metaidentifier: The prefix in the external registry
        :param normalize: Should external prefixes be normalized during lookup (e.g., lowercased)
        :return: The bioregistry prefix (if it can be mapped)

        >>> from bioregistry import manager
        >>> manager.lookup_from("obofoundry", "GO")
        'go'
        >>> manager.lookup_from("obofoundry", "go")
        None
        >>> manager.lookup_from("obofoundry", "go", normalize=True)
        'go'
        """
        external_id_to_bioregistry_id = self.get_registry_invmap(metaprefix, normalize=normalize)
        return external_id_to_bioregistry_id.get(
            _norm(metaidentifier) if normalize else metaidentifier
        )

    def get_has_canonical(self, prefix: str) -> Optional[str]:
        """Get the canonical prefix."""
        resource = self.get_resource(prefix)
        if resource is None:
            return None
        return resource.has_canonical

    def get_canonical_for(self, prefix: str) -> Optional[List[str]]:
        """Get the prefixes for which this is annotated as canonical."""
        norm_prefix = self.normalize_prefix(prefix)
        if norm_prefix is None:
            return None
        return self.canonical_for.get(norm_prefix, [])

    def get_provides_for(self, prefix: str) -> Optional[str]:
        """Get the resource that the given prefix provides for, or return none if not a provider."""
        resource = self.get_resource(prefix)
        if resource is None:
            return None
        return resource.provides

    def get_provided_by(self, prefix: str) -> Optional[List[str]]:
        """Get the resources that provide for the given prefix, or return none if the prefix can't be looked up."""
        norm_prefix = self.normalize_prefix(prefix)
        if norm_prefix is None:
            return None
        return self.provided_by.get(norm_prefix, [])

    def get_part_of(self, prefix: str) -> Optional[str]:
        """Get the parent resource, if annotated."""
        resource = self.get_resource(prefix)
        if resource is None:
            return None
        return resource.part_of

    def get_has_parts(self, prefix: str) -> Optional[List[str]]:
        """Get the children resources, if annotated."""
        norm_prefix = self.normalize_prefix(prefix)
        if norm_prefix is None:
            return None
        return self.has_parts.get(norm_prefix, [])

    def get_parts_collections(self) -> Mapping[str, List[str]]:
        """Group resources' prefixes based on their ``part_of`` entries.

        :returns:
            A dictionary with keys that appear as the values of ``Resource.part_of``
            and whose values are lists of prefixes for resources that have the key
            as a value in its ``part_of`` field.

        .. warning::

            Many of the keys in this dictionary are valid Bioregistry prefixes,
            but this is not necessary. For example, ``ctd`` is one key that
            appears that explicitly has no prefix, since it corresponds to a
            resource and not a vocabulary.
        """
        rv = {}
        for key, values in self.has_parts.items():
            norm_key = self.normalize_prefix(key)
            if norm_key is None:
                rv[key] = list(values)
            else:
                rv[key] = [norm_key, *values]
        return rv

    def get_bioregistry_iri(self, prefix: str, identifier: str) -> Optional[str]:
        """Get a Bioregistry link.

        :param prefix: The prefix in the CURIE
        :param identifier: The identifier in the CURIE
        :return: A link to the Bioregistry resolver
        """
        norm_prefix, norm_identifier = self.normalize_parsed_curie(prefix, identifier)
        if norm_prefix is None or norm_identifier is None:
            return None
        return f"{BIOREGISTRY_REMOTE_URL.rstrip()}/{curie_to_str(norm_prefix, norm_identifier)}"

    def get_default_iri(self, prefix: str, identifier: str) -> Optional[str]:
        """Get the default URL for the given CURIE.

        :param prefix: The prefix in the CURIE
        :param identifier: The identifier in the CURIE
        :return: A IRI string corresponding to the default provider, if available.

        >>> from bioregistry import manager
        >>> manager.get_default_iri('chebi', '24867')
        'https://www.ebi.ac.uk/chebi/searchId.do?chebiId=CHEBI:24867'
        """
        entry = self.get_resource(prefix)
        if entry is None:
            return None
        return entry.get_default_uri(identifier)

    def get_miriam_curie(self, prefix: str, identifier: str) -> Optional[str]:
        """Get the identifiers.org CURIE for the given CURIE."""
        resource = self.get_resource(prefix)
        if resource is None:
            return None
        return resource.get_miriam_curie(identifier)

    def get_miriam_iri(self, prefix: str, identifier: str) -> Optional[str]:
        """Get the identifiers.org URL for the given CURIE.

        :param prefix: The prefix in the CURIE
        :param identifier: The identifier in the CURIE
        :return: A IRI string corresponding to the Identifiers.org, if the prefix exists and is
            mapped to MIRIAM.
        """
        curie = self.get_miriam_curie(prefix, identifier)
        if curie is None:
            return None
        return f"{IDENTIFIERS_ORG_URL_PREFIX}{curie}"

    def get_bioportal_iri(self, prefix: str, identifier: str) -> Optional[str]:
        """Get the Bioportal URL for the given CURIE.

        :param prefix: The prefix in the CURIE
        :param identifier: The identifier in the CURIE
        :return: A link to the Bioportal page

        >>> from bioregistry import manager
        >>> manager.get_bioportal_iri('chebi', '24431')
        'https://bioportal.bioontology.org/ontologies/CHEBI/?p=classes&conceptid=http://purl.obolibrary.org/obo/CHEBI_24431'
        """
        bioportal_prefix = self.get_mapped_prefix(prefix, "bioportal")
        if bioportal_prefix is None:
            return None
        obo_link = self.get_obofoundry_iri(prefix, identifier)
        if obo_link is not None:
            return f"https://bioportal.bioontology.org/ontologies/{bioportal_prefix}/?p=classes&conceptid={obo_link}"
        # TODO there must be other rules?
        return None

    def get_ols_iri(self, prefix: str, identifier: str) -> Optional[str]:
        """Get the OLS URL if possible."""
        ols_prefix = self.get_mapped_prefix(prefix, "ols")
        obo_iri = self.get_obofoundry_iri(prefix, identifier)
        if ols_prefix is None or obo_iri is None:
            return None
        return f"https://www.ebi.ac.uk/ols/ontologies/{ols_prefix}/terms?iri={obo_iri}"

    def get_formatted_iri(self, metaprefix: str, prefix: str, identifier: str) -> Optional[str]:
        """Get an IRI using the format in the metaregistry.

        :param metaprefix: The metaprefix of the registry in the metaregistry
        :param prefix: A bioregistry prefix (will be mapped to the external one automatically)
        :param identifier: The identifier for the entity
        :returns: An IRI generated from the ``resolver_url`` format string of the registry, if it
            exists.

        >>> from bioregistry import manager
        >>> manager.get_formatted_iri("miriam", "hgnc", "16793")
        'https://identifiers.org/hgnc:16793'
        >>> manager.get_formatted_iri("n2t", "hgnc", "16793")
        'https://n2t.net/hgnc:16793'
        >>> manager.get_formatted_iri("obofoundry", "fbbt", "00007294")
        'http://purl.obolibrary.org/obo/FBbt_00007294'
        """
        mapped_prefix = self.get_mapped_prefix(prefix, metaprefix)
        registry = self.metaregistry.get(metaprefix)
        if registry is None or mapped_prefix is None:
            return None
        return registry.resolve(mapped_prefix, identifier)

    def get_obofoundry_iri(self, prefix: str, identifier: str) -> Optional[str]:
        """Get the OBO Foundry URL if possible.

        :param prefix: The prefix
        :param identifier: The identifier
        :return: The OBO Foundry URL if the prefix can be mapped to an OBO Foundry entry

        >>> from bioregistry import manager
        >>> manager.get_obofoundry_iri('chebi', '24431')
        'http://purl.obolibrary.org/obo/CHEBI_24431'

        For entries where there's a preferred prefix, it is respected.

        >>> manager.get_obofoundry_iri('fbbt', '00007294')
        'http://purl.obolibrary.org/obo/FBbt_00007294'
        """
        return self.get_formatted_iri("obofoundry", prefix, identifier)

    def get_n2t_iri(self, prefix: str, identifier: str) -> Optional[str]:
        """Get the name-to-thing URL for the given CURIE.

        :param prefix: The prefix in the CURIE
        :param identifier: The identifier in the CURIE
        :return: A IRI string corresponding to the N2T resolve, if the prefix exists and is
            mapped to N2T.

        >>> from bioregistry import manager
        >>> manager.get_n2t_iri("chebi", "24867")
        'https://n2t.net/chebi:24867'
        """
        return self.get_formatted_iri("n2t", prefix, identifier)

    def get_scholia_iri(self, prefix: str, identifier: str) -> Optional[str]:
        """Get a Scholia IRI, if possible.

        :param prefix: The prefix in the CURIE
        :param identifier: The identifier in the CURIE
        :return: A link to the Scholia page

        >>> from bioregistry import manager
        >>> manager.get_scholia_iri("pubmed", "1234")
        'https://scholia.toolforge.org/pubmed/1234'

        >>> manager.get_scholia_iri("pdb", "1234")
        None
        """
        resource = self.get_resource(prefix)
        if resource is None:
            return None
        for provider in resource.get_extra_providers():
            if provider.code == "scholia":
                return provider.resolve(identifier)
        return None

    def get_provider_functions(self) -> Mapping[str, Callable[[str, str], Optional[str]]]:
        """Return a mapping of provider functions."""
        return {
            "default": self.get_default_iri,
            "miriam": self.get_miriam_iri,
            "obofoundry": self.get_obofoundry_iri,
            "ols": self.get_ols_iri,
            "n2t": self.get_n2t_iri,
            "bioportal": self.get_bioportal_iri,
            "scholia": self.get_scholia_iri,
        }

    def get_providers_list(self, prefix: str, identifier: str) -> Sequence[Tuple[str, str]]:
        """Get all providers for the CURIE."""
        rv = []
        for metaprefix, get_url in self.get_provider_functions().items():
            link = get_url(prefix, identifier)
            if link is not None:
                rv.append((metaprefix, link))

        resource = self.get_resource(prefix)
        if resource is None:
            raise KeyError
        for provider in resource.get_extra_providers():
            rv.append((provider.code, provider.resolve(identifier)))

        if not rv:
            return rv

        bioregistry_link = self.get_bioregistry_iri(prefix, identifier)
        if not bioregistry_link:
            return rv

        # if a default URL is available, it goes first. otherwise the bioregistry URL goes first.
        rv.insert(1 if rv[0][0] == "default" else 0, ("bioregistry", bioregistry_link))
        return rv

    def get_providers(self, prefix: str, identifier: str) -> Dict[str, str]:
        """Get all providers for the CURIE.

        :param prefix: the prefix in the CURIE
        :param identifier: the identifier in the CURIE
        :returns: A dictionary of IRIs associated with the CURIE

        >>> from bioregistry import manager
        >>> assert "chebi-img" in manager.get_providers("chebi", "24867")
        """
        return dict(self.get_providers_list(prefix, identifier))

    def get_registry_uri(self, metaprefix: str, prefix: str, identifier: str) -> Optional[str]:
        """Get the URL to resolve the given prefix/identifier pair with the given resolver."""
        providers = self.get_providers(prefix, identifier)
        if not providers:
            return None
        return providers.get(metaprefix)

    def get_iri(
        self,
        prefix: str,
        identifier: Optional[str] = None,
        *,
        priority: Optional[Sequence[str]] = None,
        prefix_map: Optional[Mapping[str, str]] = None,
        use_bioregistry_io: bool = True,
        provider: Optional[str] = None,
    ) -> Optional[str]:
        """Get the best link for the CURIE pair, if possible.

        :param prefix: The prefix in the CURIE
        :param identifier: The identifier in the CURIE. If identifier is given as None, then this function will
            assume that the first argument (``prefix``) is actually a full CURIE.
        :param priority: A user-defined priority list. In addition to the metaprefixes in the Bioregistry
            corresponding to resources that are resolvers/lookup services, you can also use ``default``
            to correspond to the first-party IRI and ``custom`` to refer to the custom prefix map.
            The default priority list is:

            1. Custom prefix map (``custom``)
            1. First-party IRI (``default``)
            2. Identifiers.org / MIRIAM (``miriam``)
            3. Ontology Lookup Service (``ols``)
            4. OBO PURL (``obofoundry``)
            5. Name-to-Thing (``n2t``)
            6. BioPortal (``bioportal``)
        :param prefix_map: A custom prefix map to go with the ``custom`` key in the priority list
        :param use_bioregistry_io: Should the bioregistry resolution IRI be used? Defaults to true.
        :param provider: The provider code to use for a custom provider
        :return: The best possible IRI that can be generated based on the priority list.

        A pre-parse CURIE can be given as the first two arguments
        >>> from bioregistry import manager
        >>> manager.get_iri("chebi", "24867")
        'https://www.ebi.ac.uk/chebi/searchId.do?chebiId=CHEBI:24867'

        A CURIE can be given directly as a single argument
        >>> manager.get_iri("chebi:24867")
        'https://www.ebi.ac.uk/chebi/searchId.do?chebiId=CHEBI:24867'

        A priority list can be given
        >>> priority = ["obofoundry", "default", "bioregistry"]
        >>> manager.get_iri("chebi:24867", priority=priority)
        'http://purl.obolibrary.org/obo/CHEBI_24867'

        A custom prefix map can be supplied.
        >>> prefix_map = {"chebi": "https://example.org/chebi/"}
        >>> manager.get_iri("chebi:24867", prefix_map=prefix_map)
        'https://example.org/chebi/24867'
        >>> manager.get_iri("fbbt:00007294")
        'https://flybase.org/cgi-bin/cvreport.pl?id=FBbt:00007294'

        A custom prefix map can be supplied in combination with a priority list
        >>> prefix_map = {"lipidmaps": "https://example.org/lipidmaps/"}
        >>> priority = ["obofoundry", "custom", "default", "bioregistry"]
        >>> manager.get_iri("chebi:24867", prefix_map=prefix_map, priority=priority)
        'http://purl.obolibrary.org/obo/CHEBI_24867'
        >>> manager.get_iri("lipidmaps:1234", prefix_map=prefix_map, priority=priority)
        'https://example.org/lipidmaps/1234'

        A custom provider is given, which makes the Bioregistry very extensible
        >>> manager.get_iri("chebi:24867", provider="chebi-img")
        'https://www.ebi.ac.uk/chebi/displayImage.do?defaultImage=true&imageIndex=0&chebiId=24867'
        """
        if identifier is None:
            _prefix, _identifier = self.parse_curie(prefix)
            if _prefix is None or _identifier is None:
                return None
        else:
            _prefix, _identifier = prefix, identifier

        providers = self.get_providers(_prefix, _identifier)
        if provider is not None:
            if provider not in providers:
                return None
            return providers[provider]
        if prefix_map and _prefix in prefix_map:
            providers["custom"] = f"{prefix_map[_prefix]}{_identifier}"
        for key in priority or LINK_PRIORITY:
            if not use_bioregistry_io and key == "bioregistry":
                continue
            if key not in providers:
                continue
            rv = providers[key]
            if rv is not None:
                return rv
        return None

    def get_internal_prefix_map(self) -> Mapping[str, str]:
        """Get an internal prefix map for RDF and SSSOM dumps."""
        default_prefixes = {"bioregistry.schema", "bfo"}
        rv = cast(
            Dict[str, str], {prefix: self.get_uri_prefix(prefix) for prefix in default_prefixes}
        )
        for metaprefix, metaresource in self.metaregistry.items():
            uri_prefix = metaresource.get_provider_uri_prefix()
            if metaresource.bioregistry_prefix:
                rv[metaresource.bioregistry_prefix] = uri_prefix
            else:
                rv[metaprefix] = uri_prefix
        return rv

    def is_novel(self, prefix: str) -> Optional[bool]:
        """Check if the prefix is novel to the Bioregistry, i.e., it has no external mappings."""
        resource = self.get_resource(prefix)
        if resource is None:
            return None
        return not resource.get_mappings()

    def count_mappings(self, include_bioregistry: bool = True) -> typing.Counter[str]:
        """Count the mappings for each registry."""
        rv = Counter(
            metaprefix
            for resource in self.registry.values()
            for metaprefix in resource.get_mappings()
        )
        if include_bioregistry:
            rv["bioregistry"] = len(self.registry)
        return rv

    def is_valid_identifier(self, prefix: str, identifier: str) -> bool:
        """Check if the pre-parsed CURIE is standardized valid.

        :param prefix: The prefix from a compact URI
        :param identifier: The local unique identifer from a compact URI
        :return:
            If the CURIE is standardized in both syntax and semantics. This means that it uses the Bioregistry
            canonical prefix, does not have a redundant prefix, and if available, matches the Bioregistry's
            regular expression pattern for identifiers.

        Standard CURIE
        >>> from bioregistry import manager
        >>> manager.is_valid_identifier("go", "0000001")
        True

        Non-standardized prefix
        >>> manager.is_valid_identifier("GO", "0000001")
        False

        Incorrect identifier
        >>> manager.is_valid_identifier("go", "0001")
        False

        Banana scenario
        >>> manager.is_valid_identifier("go", "GO:0000001")
        False

        Unknown prefix
        >>> manager.is_valid_identifier("xxx", "yyy")
        False
        """
        resource = self.registry.get(prefix)
        if resource is None:
            return False
        return resource.is_valid_identifier(identifier)

    def is_standardizable_identifier(self, prefix: str, identifier: str) -> bool:
        """Check if the identifier is standardizable.

        :param prefix: The prefix from a compact URI
        :param identifier: The local unique identifer from a compact URI
        :return:
            If the CURIE can be standardized (e.g., prefix normalize and identifier normalized)
            then validated.

        Standard CURIE
        >>> from bioregistry import manager
        >>> manager.is_standardizable_identifier("go", "0000001")
        True

        Non-standardized prefix
        >>> manager.is_standardizable_identifier("GO", "0000001")
        True

        Incorrect identifier
        >>> manager.is_standardizable_identifier("go", "0001")
        False

        Banana scenario
        >>> manager.is_standardizable_identifier("go", "GO:0000001")
        True

        Unknown prefix
        >>> manager.is_standardizable_identifier("xxx", "yyy")
        False
        """
        resource = self.get_resource(prefix)
        if resource is None:
            return False
        return resource.is_standardizable_identifier(identifier)

    def is_valid_curie(self, curie: str) -> bool:
        """Check if a CURIE is standardized and valid.

        :param curie: A compact URI of the form ``<prefix>:<local unique identifier>``.
        :return:
            If the CURIE is standardized in both syntax and semantics. This means that it uses the Bioregistry
            canonical prefix, does not have a redundant prefix, and if available, matches the Bioregistry's
            regular expression pattern for identifiers.

        Standard CURIE
        >>> from bioregistry import manager
        >>> manager.is_valid_curie("go:0000001")
        True

        Not a standard CURIE (i.e., no colon)
        >>> manager.is_valid_curie("0000001")
        False
        >>> manager.is_valid_curie("GO_0000001")
        False
        >>> manager.is_valid_curie("PTM-0001")
        False

        Non-standardized prefix
        >>> manager.is_valid_curie("GO:0000001")
        False

        Incorrect identifier
        >>> manager.is_valid_curie("go:0001")
        False

        Banana scenario
        >>> manager.is_valid_curie("go:GO:0000001")
        False

        Unknown prefix
        >>> manager.is_valid_curie("xxx:yyy")
        False
        """
        try:
            prefix, identifier = curie.split(":", 1)
        except ValueError:
            return False
        return self.is_valid_identifier(prefix, identifier)

    def is_standardizable_curie(self, curie: str) -> bool:
        """Check if a CURIE is validatable, but not necessarily standardized.

        :param curie: A compact URI
        :return: If the CURIE can be standardized (e.g., prefix normalize and identifier normalized)
            then validated.

        Standard CURIE
        >>> from bioregistry import manager
        >>> manager.is_standardizable_curie("go:0000001")
        True

        Not a standard CURIE (i.e., no colon)
        >>> manager.is_standardizable_curie("0000001")
        False
        >>> manager.is_standardizable_curie("GO_0000001")
        False
        >>> manager.is_standardizable_curie("PTM-0001")
        False

        Non-standardized prefix
        >>> manager.is_standardizable_curie("GO:0000001")
        True

        Incorrect identifier
        >>> manager.is_standardizable_curie("go:0001")
        False

        Banana scenario
        >>> manager.is_standardizable_curie("go:GO:0000001")
        True

        Unknown prefix
        >>> manager.is_standardizable_curie("xxx:yyy")
        False
        """
        try:
            prefix, identifier = curie.split(":", 1)
        except ValueError:
            return False
        return self.is_standardizable_identifier(prefix, identifier)

    def get_context(self, key: str) -> Optional[Context]:
        """Get a prescriptive context.

        :param key: The identifier for the prescriptive context, e.g., `obo`.
        :returns: A prescriptive context object, if available
        """
        return self.contexts.get(key)

    def get_context_artifacts(
        self, key: str, include_synonyms: Optional[bool] = None
    ) -> Tuple[Mapping[str, str], Mapping[str, str]]:
        """Get a prescriptive prefix map and pattern map."""
        context = self.get_context(key)
        if context is None:
            raise KeyError
        include_synonyms = (
            include_synonyms if include_synonyms is not None else context.include_synonyms
        )
        prescriptive_prefix_map = self.get_prefix_map(
            remapping=context.prefix_remapping,
            uri_prefix_priority=context.uri_prefix_priority,
            prefix_priority=context.prefix_priority,
            include_synonyms=include_synonyms,
            blacklist=context.blacklist,
        )
        prescriptive_pattern_map = self.get_pattern_map(
            remapping=context.prefix_remapping,
            include_synonyms=include_synonyms,
            prefix_priority=context.prefix_priority,
            blacklist=context.blacklist,
        )
        return prescriptive_prefix_map, prescriptive_pattern_map

    def get_obo_health_url(self, prefix: str) -> Optional[str]:
        """Get the OBO community health badge."""
        obo_prefix = self.get_mapped_prefix(prefix, "obofoundry")
        if obo_prefix is None:
            return None
        obo_pp = manager.get_preferred_prefix(prefix)
        return f"{SHIELDS_BASE}/json?url={HEALTH_BASE}&query=$.{obo_prefix.lower()}.score&label={obo_pp}{EXTRAS}"

    def read_contributors(self, direct_only: bool = False) -> Mapping[str, Attributable]:
        """Get a mapping from contributor ORCID identifiers to author objects."""
        return _read_contributors(
            registry=self.registry,
            metaregistry=self.metaregistry,
            collections=self.collections,
            contexts=self.contexts,
            direct_only=direct_only,
        )


def prepare_prefix_list(prefix_map: Mapping[str, str]) -> List[Tuple[str, str]]:
    """Prepare a priority prefix list from a prefix map."""
    rv = []
    for prefix, uri_prefix in sorted(prefix_map.items(), key=_sort_key):
        rv.append((prefix, uri_prefix))
        if uri_prefix.startswith("https://"):
            rv.append((prefix, "http://" + uri_prefix[8:]))
        elif uri_prefix.startswith("http://"):
            rv.append((prefix, "https://" + uri_prefix[7:]))
    return rv


def _sort_key(kv: Tuple[str, str]) -> int:
    """Return a value appropriate for sorting a pair of prefix/IRI."""
    return -len(kv[0])


def _read_contributors(
    registry, metaregistry, collections, contexts, direct_only: bool = False
) -> Mapping[str, Attributable]:
    """Get a mapping from contributor ORCID identifiers to author objects."""
    rv: Dict[str, Attributable] = {}
    for resource in registry.values():
        if resource.contributor and resource.contributor.orcid:
            rv[resource.contributor.orcid] = resource.contributor
        for contributor in resource.contributor_extras or []:
            if contributor.orcid:
                rv[contributor.orcid] = contributor
        if resource.reviewer and resource.reviewer.orcid:
            rv[resource.reviewer.orcid] = resource.reviewer
        if not direct_only:
            contact = resource.get_contact()
            if contact and contact.orcid:
                rv[contact.orcid] = contact
    for metaresource in metaregistry.values():
        if not direct_only:
            if metaresource.contact.orcid:
                rv[metaresource.contact.orcid] = metaresource.contact
    for collection in collections.values():
        for author in collection.authors or []:
            if author.orcid:
                rv[author.orcid] = author
    for context in contexts.values():
        for maintainer in context.maintainers:
            if maintainer.orcid:
                rv[maintainer.orcid] = maintainer
    return rv


#: The default manager for the Bioregistry
manager = Manager()
