# -*- coding: utf-8 -*-

"""A class-based client to a metaregistry."""

import logging
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple, Union

from .schema import Resource
from .utils import NormDict, curie_to_str, read_registry, write_registry

__all__ = [
    "ResourceManager",
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


class ResourceManager:
    """A manager for functionality related to a metaregistry."""

    def __init__(self, registry: Optional[Mapping[str, Resource]] = None):
        """Instantiate a registry manager.

        :param registry: A custom registry. If none given, defaults to the Bioregistry.
        """
        if registry is None:
            registry = read_registry()
        self.registry = registry
        self.synonyms = _synonym_to_canonical(registry)

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

    def get_registry_map(self, metaprefix: str) -> Dict[str, str]:
        """Get a mapping from the Bioregistry prefixes to prefixes in another registry."""
        return dict(self._iter_registry_map(metaprefix))

    def get_registry_invmap(self, metaprefix: str) -> Dict[str, str]:
        """Get a mapping from prefixes in another registry to Bioregistry prefixes."""
        return {metaprefix: prefix for prefix, metaprefix in self._iter_registry_map(metaprefix)}

    def _iter_registry_map(self, metaprefix: str) -> Iterable[Tuple[str, str]]:
        for prefix, resource in self.registry.items():
            mapped_prefix = resource.get_mapped_prefix(metaprefix)
            if mapped_prefix is not None:
                yield prefix, mapped_prefix

    def get_external(self, prefix: str, metaprefix: str) -> Mapping[str, Any]:
        """Get the external data for the entry."""
        entry = self.get_resource(prefix)
        if entry is None:
            return {}
        return entry.get_external(metaprefix)

    def get_versions(self) -> Mapping[str, str]:
        """Get a map of prefixes to versions."""
        rv = {}
        for prefix in self.registry:
            version = self.get_external(prefix, "ols").get("version")
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

        :param prefix: The prefix to to look up
        :return: The regular expression pattern to match CURIEs against
        """
        resource = self.get_resource(prefix)
        if resource is None:
            return None
        pattern = resource.get_pattern()
        if pattern is None:
            return None
        p = resource.get_preferred_prefix() or prefix
        return f"^{p}:{pattern.lstrip('^')}"


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
