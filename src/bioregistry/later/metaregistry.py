# -*- coding: utf-8 -*-

"""Load the manually curated metaregistry."""

import json
from functools import lru_cache
from typing import List, Mapping, Set, Tuple

from .constants import CURATED_REGISTRY_PATH


@lru_cache()
def _get_curated_registry(rewrite: bool = True):
    """Get the metaregistry."""
    with open(CURATED_REGISTRY_PATH) as file:
        x = json.load(file)
    if rewrite:
        with open(CURATED_REGISTRY_PATH, 'w') as file:
            json.dump(x, file, indent=2, sort_keys=True)
    return x


@lru_cache()
def get_curated_registry_database():
    """Get the curated metaregistry."""
    return _get_curated_registry()['database']


@lru_cache()
def get_wikidata_property_types() -> List[str]:
    """Get the wikidata property types."""
    return _get_curated_registry()['wikidata_property_types']


@lru_cache()
def get_not_available_as_obo():
    """Get the list of prefixes not available as OBO."""
    #: A list of prefixes that have been manually annotated as not being available in OBO
    return {
        prefix
        for prefix, entry in get_curated_registry_database().items()
        if 'not_available_as_obo' in entry and entry['not_available_as_obo']
    }


@lru_cache()
def get_curated_urls() -> Mapping[str, str]:
    """Get a mapping of prefixes to their custom download URLs."""
    #: URLs of resources that weren't listed in OBO Foundry properly
    return {
        k: v['download']
        for k, v in get_curated_registry_database().items()
        if 'download' in v
    }


@lru_cache()
def get_xrefs_prefix_blacklist() -> Set[str]:
    """Get the set of blacklisted xref prefixes."""
    #: Xrefs starting with these prefixes will be ignored
    return set(_get_curated_registry()['blacklists']['prefix'])


@lru_cache()
def get_xrefs_suffix_blacklist() -> Set[str]:
    """Get the set of blacklisted xref suffixes."""
    #: Xrefs ending with these suffixes will be ignored
    return set(_get_curated_registry()['blacklists']['suffix'])


@lru_cache()
def get_xrefs_blacklist() -> Set[str]:
    """Get the set of blacklisted xrefs."""
    return set(_get_curated_registry()['blacklists']['full'])


@lru_cache()
def get_obsolete():
    """Get the set of prefixes that have been manually annotated as obsolete."""
    return _get_curated_registry()['obsolete']


@lru_cache()
def get_remappings_full():
    """Get the remappings for xrefs based on the entire xref database."""
    return _get_curated_registry()['remappings']['full']


@lru_cache()
def get_remappings_prefix():
    """Get the remappings for xrefs based on the prefix.

    .. note:: Doesn't take into account the semicolon `:`
    """
    return _get_curated_registry()['remappings']['prefix']


@lru_cache()
def get_prefix_to_miriam_prefix() -> Mapping[str, Tuple[str, str]]:
    """Get a mapping of prefixes to MIRIAM prefixes."""
    return {
        prefix: (entry['miriam']['prefix'], entry['miriam']['namespaceEmbeddedInLui'])
        for prefix, entry in get_curated_registry_database().items()
        if 'miriam' in entry
    }
