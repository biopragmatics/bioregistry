# -*- coding: utf-8 -*-

"""A class-based client to a metaregistry."""

import logging
from collections import defaultdict
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

from .constants import (
    BIOREGISTRY_REMOTE_URL,
    IDENTIFIERS_ORG_URL_PREFIX,
    LINK_PRIORITY,
    MIRIAM_BLACKLIST,
)
from .license_standardizer import standardize_license
from .schema import Registry, Resource, sanitize_model
from .schema_utils import (
    _registry_from_path,
    read_metaregistry,
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

    def __init__(
        self,
        registry: Optional[Mapping[str, Resource]] = None,
        metaregistry: Optional[Mapping[str, Registry]] = None,
    ):
        """Instantiate a registry manager.

        :param registry: A custom registry. If none given, defaults to the Bioregistry.
        :param metaregistry: A custom metaregistry. If none, defaults to the Bioregistry's metaregistry.
        """
        self.registry = dict(read_registry() if registry is None else registry)
        self.synonyms = _synonym_to_canonical(self.registry)

        self.metaregistry = dict(read_metaregistry() if metaregistry is None else metaregistry)

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

    @classmethod
    def from_path(cls, path: Union[str, Path]) -> "Manager":
        """Load a manager from the given path."""
        return cls(_registry_from_path(path))

    def write_registry(self):
        """Write the registry."""
        write_registry(self.registry)

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
        norm_identifier = resource.standardize_identifier(identifier, prefix=prefix)
        return norm_prefix, norm_identifier

    @lru_cache(maxsize=None)  # noqa:B019
    def get_registry_map(self, metaprefix: str) -> Dict[str, str]:
        """Get a mapping from the Bioregistry prefixes to prefixes in another registry."""
        return dict(self._iter_registry_map(metaprefix))

    @lru_cache(maxsize=None)  # noqa:B019
    def get_registry_invmap(self, metaprefix: str, normalize: bool = False) -> Dict[str, str]:
        """Get a mapping from prefixes in another registry to Bioregistry prefixes."""
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
        include_synonyms: bool = False,
        remapping: Optional[Mapping[str, str]] = None,
        use_preferred: bool = False,
    ) -> Mapping[str, str]:
        """Get a mapping from prefixes to their regular expression patterns.

        :param include_synonyms: Should synonyms of each prefix also be included as additional prefixes, but with
            the same URI prefix?
        :param remapping: A mapping from prefixes to preferred prefixes.
        :param use_preferred: Should preferred prefixes be used? Set this to true if you're in the OBO context.
        :return: A mapping from prefixes to regular expression pattern strings.
        """
        it = self._iter_pattern_map(include_synonyms=include_synonyms, use_preferred=use_preferred)
        if not remapping:
            return dict(it)
        return {remapping.get(prefix, prefix): uri_prefix for prefix, uri_prefix in it}

    def _iter_pattern_map(
        self,
        *,
        include_synonyms: bool = False,
        use_preferred: bool = False,
    ) -> Iterable[Tuple[str, str]]:
        for prefix, resource in self.registry.items():
            pattern = resource.get_pattern()
            if pattern is None:
                continue
            if use_preferred:
                preferred_prefix = resource.get_preferred_prefix()
                if preferred_prefix is not None:
                    prefix = preferred_prefix
            yield prefix, pattern
            if include_synonyms:
                for synonym in resource.get_synonyms():
                    yield synonym, pattern

    def get_prefix_map(
        self,
        *,
        priority: Optional[Sequence[str]] = None,
        include_synonyms: bool = False,
        remapping: Optional[Mapping[str, str]] = None,
        use_preferred: bool = False,
    ) -> Mapping[str, str]:
        """Get a mapping from Bioregistry prefixes to their URI prefixes .

        :param priority: A priority list for how to generate URI prefixes.
        :param include_synonyms: Should synonyms of each prefix also be included as additional prefixes, but with
            the same URI prefix?
        :param remapping: A mapping from Bioregistry prefixes to preferred prefixes.
        :param use_preferred: Should preferred prefixes be used? Set this to true if you're in the OBO context.
        :return: A mapping from prefixes to URI prefixes.
        """
        it = self._iter_prefix_map(
            priority=priority, include_synonyms=include_synonyms, use_preferred=use_preferred
        )
        if not remapping:
            return dict(it)
        return {remapping.get(prefix, prefix): uri_prefix for prefix, uri_prefix in it}

    def _iter_prefix_map(
        self,
        *,
        priority: Optional[Sequence[str]] = None,
        include_synonyms: bool = False,
        use_preferred: bool = False,
    ) -> Iterable[Tuple[str, str]]:
        for prefix, resource in self.registry.items():
            uri_prefix = resource.get_uri_prefix(priority=priority)
            if uri_prefix is None:
                continue
            if use_preferred:
                preferred_prefix = resource.get_preferred_prefix()
                if preferred_prefix is not None:
                    prefix = preferred_prefix
            yield prefix, uri_prefix
            if include_synonyms:
                for synonym in resource.get_synonyms():
                    yield synonym, uri_prefix

    def get_prefix_list(self, **kwargs) -> List[Tuple[str, str]]:
        """Get the default priority prefix list."""
        #: A prefix map in reverse sorted order based on length of the URI prefix
        #: in order to avoid conflicts of sub-URIs (thanks to Nico Matentzoglu for the idea)
        return prepare_prefix_list(self.get_prefix_map(**kwargs))

    def get_curie_pattern(self, prefix: str) -> Optional[str]:
        """Get the CURIE pattern for this resource.

        :param prefix: The prefix to look up
        :return: The regular expression pattern to match CURIEs against
        """
        resource = self.get_resource(prefix)
        if resource is None:
            return None
        pattern = resource.get_pattern()
        if pattern is None:
            return None
        p = resource.get_preferred_prefix() or prefix
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
            prefix: self._rasterized_resource(prefix, resource)
            for prefix, resource in self.registry.items()
        }

    def _rasterized_resource(self, prefix: str, resource: Resource) -> Resource:
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
            # Registry properties
            example=resource.get_example(),
            example_extras=resource.example_extras,
            uri_format=resource.get_uri_format(),
            providers=resource.get_extra_providers(),
            # Comments
            comment=resource.comment,
            references=resource.references,
            # MIRIAM compatibility
            banana=resource.get_banana(),
            namespace_in_lui=resource.get_namespace_in_lui(),
            # Provenance
            contact=resource.get_contact(),
            contributor=resource.contributor,
            reviewer=resource.reviewer,
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

    def get_bioregistry_iri(self, prefix: str, identifier: str) -> Optional[str]:
        """Get a Bioregistry link.

        :param prefix: The prefix in the CURIE
        :param identifier: The identifier in the CURIE
        :return: A link to the Bioregistry resolver
        """
        norm_prefix, norm_identifier = self.normalize_parsed_curie(prefix, identifier)
        if norm_prefix is None:
            return None
        return f"{BIOREGISTRY_REMOTE_URL.rstrip()}/{norm_prefix}:{norm_identifier}"

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
        miriam_prefix = self.get_mapped_prefix(prefix, "miriam")
        if miriam_prefix is None or miriam_prefix in MIRIAM_BLACKLIST:
            return None
        banana = resource.get_banana()
        if banana:
            if identifier.startswith(f"{banana}:"):
                return identifier
            else:
                return f"{banana}:{identifier}"
        elif resource.get_namespace_in_lui():
            if identifier.startswith(prefix.upper()):
                return identifier
            else:
                return f"{prefix.upper()}:{identifier}"
        else:
            return f"{miriam_prefix}:{identifier}"

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
        >>> manager.get_formatted_iri("scholia", "lipidmaps", "00000052")
        'https://scholia.toolforge.org/lipidmaps/00000052'
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
        return self.get_formatted_iri("scholia", prefix, identifier)

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
        for provider, get_url in self.get_provider_functions().items():
            link = get_url(prefix, identifier)
            if link is not None:
                rv.append((provider, link))
        if not rv:
            return rv

        bioregistry_link = self.get_bioregistry_iri(prefix, identifier)
        if not bioregistry_link:
            return rv

        # if a default URL is available, it goes first. otherwise the bioregistry URL goes first.
        rv.insert(1 if rv[0][0] == "default" else 0, ("bioregistry", bioregistry_link))
        return rv

    def get_providers(self, prefix: str, identifier: str) -> Dict[str, str]:
        """Get all providers for the CURIE."""
        return dict(self.get_providers_list(prefix, identifier))

    def get_iri(
        self,
        prefix: str,
        identifier: Optional[str] = None,
        *,
        priority: Optional[Sequence[str]] = None,
        prefix_map: Optional[Mapping[str, str]] = None,
        use_bioregistry_io: bool = True,
    ) -> Optional[str]:
        """Get the best link for the CURIE, if possible.

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
        """
        if identifier is None:
            _prefix, _identifier = self.parse_curie(prefix)
            if _prefix is None or _identifier is None:
                return None
        else:
            _prefix, _identifier = prefix, identifier

        providers = self.get_providers(_prefix, _identifier)
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


#: The default manager for the Bioregistry
manager = Manager()
