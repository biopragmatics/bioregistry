# -*- coding: utf-8 -*-

"""Utilities for normalizing prefixes."""

from functools import lru_cache
from typing import Any, Mapping, Optional

from .utils import read_bioregistry

__all__ = [
    'get',
    'get_pattern',
    'is_deprecated',
    'normalize_prefix',
]


def get(prefix: str) -> Optional[Mapping[str, Any]]:
    """Get the entry for the given prefix.

    :param prefix: The prefix to look up, which is normalized with :func:`normalize_prefix`
        before lookup in the Bioregistry
    :returns: The Bioregistry entry dictionary, which includes several keys cross-referencing
        other registries when available.
    """
    return read_bioregistry().get(normalize_prefix(prefix))


def get_pattern(prefix: str) -> Optional[str]:
    """Get the pattern for the given prefix, if it's available.

    Uses the following order of preference:

    1. Custom
    2. MIRIAM
    3. Wikidata
    """
    entry = get(prefix)
    if entry is not None:
        return (
            entry.get('pattern')
            or entry.get('miriam', {}).get('pattern')
            or entry.get('wikidata', {}).get('pattern')
        )


def is_deprecated(prefix: str) -> bool:
    """Return if the given prefix corresponds to a deprecated resource."""
    entry = get(prefix)
    if entry is None:
        return False
    if 'deprecated' in entry:
        return entry['deprecated']
    for key in ('obofoundry', 'ols', 'miriam'):
        if key in entry and 'deprecated' in entry[key]:
            return entry[key]['deprecated']
    return False


def normalize_prefix(prefix: str) -> Optional[str]:
    """Get the normalized prefix, or return None if not registered.

    :param prefix: The prefix to normalize, which could come from Bioregistry,
        OBO Foundry, OLS, or any of the curated synonyms in the Bioregistry
    :returns: The canonical Bioregistry prefix, it could be looked up. This
        will usually take precedence: MIRIAM, OBO Foundry / OLS, Custom except
        in a few cases, such as NCBITaxon.

    This works for synonym prefixes, like:

    >>> assert 'ncbitaxon' == normalize_prefix('taxonomy')

    This works for common mistaken prefixes, like:

    >>> assert 'chembl.compound' == normalize_prefix('chembl')

    This works for prefixes that are often written many ways, like:

    >>> assert 'eccode' == normalize_prefix('ec-code')
    >>> assert 'eccode' == normalize_prefix('EC_CODE')
    """
    return _synonym_to_canonical().get(prefix)


def _norm(s: str) -> str:
    """Normalize a string for dictionary key usage."""
    rv = s.casefold().lower()
    for x in ' .-_./':
        rv = rv.replace(x, '')
    return rv


class NormDict(dict):
    def __setitem__(self, key: str, value: str) -> None:
        norm_key = _norm(key)
        if value is None:
            raise ValueError(f'Tried to add empty value for {key}/{norm_key}')
        if norm_key in self and self[norm_key] != value:
            raise KeyError(f'Tried to add {norm_key}/{value} when already had {norm_key}/{self[norm_key]}')
        super().__setitem__(norm_key, value)

    def __getitem__(self, item: str) -> str:
        return super().__getitem__(_norm(item))

    def get(self, key: str, default=None) -> str:
        return super().get(_norm(key), default)


@lru_cache()
def _synonym_to_canonical() -> NormDict:
    """Return a mapping from several variants of each synonym to the canonical namespace."""
    norm_synonym_to_key = NormDict()

    for bioregistry_id, entry in read_bioregistry().items():
        norm_synonym_to_key[bioregistry_id] = bioregistry_id

        for external in ('miriam', 'ols', 'wikidata', 'obofoundry'):
            if external in entry and 'prefix' in entry[external]:
                norm_synonym_to_key[entry[external]['prefix']] = bioregistry_id

        for synonym in entry.get('synonyms', []):
            norm_synonym_to_key[synonym] = bioregistry_id

    return norm_synonym_to_key
