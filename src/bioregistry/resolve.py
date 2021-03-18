# -*- coding: utf-8 -*-

"""Utilities for normalizing prefixes."""

import datetime
import logging
import re
from functools import lru_cache
from typing import Any, Mapping, Optional

from .utils import read_bioregistry

__all__ = [
    'get',
    'get_name',
    'get_pattern',
    'get_pattern_re',
    'namespace_in_lui',
    'get_format',
    'get_example',
    'is_deprecated',
    'get_email',
    'normalize_prefix',
    'get_version',
    'get_versions',
]

logger = logging.getLogger(__name__)


def get(prefix: str) -> Optional[Mapping[str, Any]]:
    """Get the entry for the given prefix.

    :param prefix: The prefix to look up, which is normalized with :func:`normalize_prefix`
        before lookup in the Bioregistry
    :returns: The Bioregistry entry dictionary, which includes several keys cross-referencing
        other registries when available.
    """
    return read_bioregistry().get(normalize_prefix(prefix))


def get_name(prefix: str) -> Optional[str]:
    """Get the name for the given prefix, it it's availble."""
    entry = get(prefix)
    if entry is None:
        return None
    name = entry.get('name')
    if name is not None:
        return name
    for key in ('miriam', 'ols', 'obofoundry', 'wikidata'):
        name = entry.get(key, {}).get('name')
        if name is not None:
            return name
    return None


def get_pattern(prefix: str) -> Optional[str]:
    """Get the pattern for the given prefix, if it's available.

    :param prefix: The prefix to look up, which is normalized with :func:`normalize_prefix`
        before lookup in the Bioregistry
    :returns: The pattern for the prefix, if it is available, using the following order of preference:
        1. Custom
        2. MIRIAM
        3. Wikidata
    """
    entry = get(prefix)
    if entry is None:
        return None
    return (
        entry.get('pattern')
        or entry.get('miriam', {}).get('pattern')
        or entry.get('wikidata', {}).get('pattern')
    )


@lru_cache()
def get_pattern_re(prefix: str):
    """Get the compiled pattern for the given prefix, if it's available."""
    pattern = get_pattern(prefix)
    if pattern is None:
        return None
    return re.compile(pattern)


def namespace_in_lui(prefix: str) -> Optional[bool]:
    """Check if the namespace should appear in the LUI."""
    entry = get(prefix)
    if entry is None:
        return None
    rv = entry.get('namespace.embedded')  # TODO is this the best tag name?
    if rv is not None:
        return rv
    return entry.get('miriam', {}).get('namespaceEmbeddedInLui')


def get_identifiers_org_prefix(prefix: str) -> Optional[str]:
    """Get the identifiers.org prefix if available."""
    return _get_mapped_prefix(prefix, 'miriam')


def get_obofoundry_prefix(prefix: str) -> Optional[str]:
    """Get the OBO Foundry prefix if available."""
    return _get_mapped_prefix(prefix, 'obofoundry')


def get_ols_prefix(prefix: str) -> Optional[str]:
    """Get the OLS prefix if available."""
    return _get_mapped_prefix(prefix, 'ols')


def _get_mapped_prefix(prefix: str, external: str) -> Optional[str]:
    entry = get(prefix)
    if entry is None:
        return None
    return entry.get(external, {}).get('prefix')


def get_banana(prefix: str) -> Optional[str]:
    """Get the optional redundant prefix to go before an identifier."""
    entry = get(prefix)
    if entry is None:
        return None
    return entry.get('banana')


def get_format(prefix: str) -> Optional[str]:
    """Get the URL format string for the given prefix, if it's available."""
    entry = get(prefix)
    if entry is None:
        return None
    url = entry.get('url')
    if url is not None:
        return url
    miriam_id = get_identifiers_org_prefix(prefix)
    if miriam_id is not None:
        if namespace_in_lui(prefix):
            # not exact solution, some less common ones don't use capitalization
            # align with the banana solution
            miriam_id = miriam_id.upper()
        return f'https://identifiers.org/{miriam_id}:$1'
    ols_id = entry.get('ols', {}).get('prefix')
    if ols_id is not None:
        purl = f'http://purl.obolibrary.org/obo/{ols_id.upper()}_$1'
        return f'https://www.ebi.ac.uk/ols/ontologies/{ols_id}/terms?iri={purl}'
    return None


def get_example(prefix: str) -> Optional[str]:
    """Get an example identifier, if it's available."""
    entry = get(prefix)
    if entry is None:
        return None
    example = entry.get('example')
    if example is not None:
        return example
    miriam_example = entry.get('miriam', {}).get('sampleId')
    if miriam_example is not None:
        return miriam_example
    return None


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


def get_email(prefix: str) -> Optional[str]:
    """Return the contact email, if available."""
    entry = get(prefix)
    if entry is None:
        return None

    for key in ('obofoundry', 'ols'):
        obo_email = entry.get(key, {}).get('contact')
        if obo_email:
            return obo_email

    return None


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


@lru_cache(maxsize=1)
def _synonym_to_canonical() -> NormDict:
    """Return a mapping from several variants of each synonym to the canonical namespace."""
    norm_synonym_to_key = NormDict()

    for bioregistry_id, entry in read_bioregistry().items():
        norm_synonym_to_key[bioregistry_id] = bioregistry_id

        for external in ('miriam', 'ols', 'wikidata', 'obofoundry', 'go'):
            if external in entry and 'prefix' in entry[external]:
                norm_synonym_to_key[entry[external]['prefix']] = bioregistry_id

        for synonym in entry.get('synonyms', []):
            norm_synonym_to_key[synonym] = bioregistry_id

    return norm_synonym_to_key


def get_version(prefix: str) -> Optional[str]:
    """Get the version."""
    norm_prefix = normalize_prefix(prefix)
    if norm_prefix is None:
        return None
    return get_versions().get(norm_prefix)


@lru_cache(maxsize=1)
def get_versions() -> Mapping[str, str]:
    """Get a map of prefixes to versions."""
    rv = {}

    for bioregistry_id, bioregistry_entry in read_bioregistry().items():
        if 'ols' not in bioregistry_entry:
            continue
        version = bioregistry_entry['ols'].get('version')
        if version is None:
            logger.warning('[%s] missing version. Contact: %s', bioregistry_id, get_email(bioregistry_id))
            continue

        version = _clean_version(bioregistry_id, version, bioregistry_entry=bioregistry_entry)
        version_type = bioregistry_entry.get('ols_version_type')
        version_date_fmt = bioregistry_entry.get('ols_version_date_format')

        if version_date_fmt:
            if version_date_fmt in {"%Y-%d-%m"}:
                logger.warning(
                    '[%s] confusing date format: %s. Contact: %s', bioregistry_id, version_date_fmt,
                    get_email(bioregistry_id),
                )
            try:
                version = datetime.datetime.strptime(version, version_date_fmt)
            except ValueError:
                logger.warning('[%s] wrong format for version %s', bioregistry_id, version)
        elif not version_type:
            logger.warning('[%s] no type for version %s', bioregistry_id, version)

        rv[bioregistry_id] = version

    return rv


def _clean_version(
    bioregistry_id: str,
    version: str,
    *,
    bioregistry_entry: Optional[Mapping[str, Any]] = None,
) -> str:
    if bioregistry_entry is None:
        bioregistry_entry = get(bioregistry_id)
    if bioregistry_entry is None:
        raise ValueError

    if version != version.strip():
        logger.warning(
            '[%s] extra whitespace in version: %s. Contact: %s',
            bioregistry_id, version, get_email(bioregistry_id),
        )
        version = version.strip()

    version_prefix = bioregistry_entry.get('ols_version_prefix')
    if version_prefix:
        if not version.startswith(version_prefix):
            raise ValueError(f'[{bioregistry_id}] version {version} does not start with prefix {version_prefix}')
        version = version[len(version_prefix):]

    if bioregistry_entry.get('ols_version_suffix_split'):
        version = version.split()[0]

    version_suffix = bioregistry_entry.get('ols_version_suffix')
    if version_suffix:
        if not version.endswith(version_suffix):
            raise ValueError(f'[{bioregistry_id}] version {version} does not end with prefix {version_suffix}')
        version = version[:-len(version_suffix)]

    return version
