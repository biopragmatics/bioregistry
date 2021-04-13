# -*- coding: utf-8 -*-

"""Utilities for normalizing prefixes."""

import datetime
import logging
import re
from functools import lru_cache
from textwrap import dedent
from typing import Any, Mapping, Optional, Sequence, Set, Tuple, Union

from .utils import read_bioregistry, read_metaregistry

__all__ = [
    'get',
    'get_name',
    'get_description',
    'get_mappings',
    'get_synonyms',
    'get_pattern',
    'get_pattern_re',
    'namespace_in_lui',
    'get_format',
    'get_example',
    'has_terms',
    'is_deprecated',
    'get_email',
    'get_homepage',
    'get_obo_download',
    'get_owl_download',
    'parse_curie',
    'normalize_prefix',
    'get_version',
    'get_versions',
    # Metaregistry stuff
    'get_registry',
    'get_registry_name',
    'get_registry_url',
    'get_registry_homepage',
]

logger = logging.getLogger(__name__)

# not a perfect email regex, but close enough
EMAIL_RE = re.compile(r'^(\w|\.|\_|\-)+[@](\w|\_|\-|\.)+[.]\w{2,5}$')


def get(prefix: str) -> Optional[Mapping[str, Any]]:
    """Get the Bioregistry entry for the given prefix.

    :param prefix: The prefix to look up, which is normalized with :func:`normalize_prefix`
        before lookup in the Bioregistry
    :returns: The Bioregistry entry dictionary, which includes several keys cross-referencing
        other registries when available.
    """
    return read_bioregistry().get(normalize_prefix(prefix))


def get_registry(metaprefix: str) -> Optional[Mapping[str, Any]]:
    """Get the metaregistry entry for the given prefix."""
    return read_metaregistry().get(metaprefix)


def get_registry_name(metaprefix: str) -> Optional[str]:
    """Get the metaregistry name for the given prefix, if it's available."""
    registry = get_registry(metaprefix)
    if registry is None:
        return None
    return registry['name']


def get_registry_homepage(metaprefix: str) -> Optional[str]:
    """Get the URL for the registry, if available."""
    return _get_registry_key(metaprefix, 'homepage')


def get_registry_description(metaprefix: str) -> Optional[str]:
    """Get the description for the registry, if available."""
    return _get_registry_key(metaprefix, 'description')


def get_registry_example(metaprefix: str) -> Optional[str]:
    """Get an example for the registry, if available."""
    return _get_registry_key(metaprefix, 'example')


def _get_registry_key(metaprefix: str, key: str):
    registry = get_registry(metaprefix)
    if registry is None:
        return None
    return registry.get(key)


def get_registry_url(metaprefix: str, prefix: str) -> Optional[str]:
    """Get the URL for the resource inside registry, if available."""
    entry = get_registry(metaprefix)
    if entry is None:
        return None
    formatter = entry.get('formatter')
    if formatter is None:
        return None
    return formatter.replace('$1', prefix)


def get_name(prefix: str) -> Optional[str]:
    """Get the name for the given prefix, it it's available."""
    return _get_prefix_key(prefix, 'name', ('obofoundry', 'ols', 'wikidata', 'go', 'ncbi', 'bioportal', 'miriam'))


def get_description(prefix: str) -> Optional[str]:
    """Get the description for the given prefix, if available."""
    return _get_prefix_key(prefix, 'description', ('miriam', 'ols', 'obofoundry', 'wikidata'))


def get_mappings(prefix: str) -> Optional[Mapping[str, str]]:
    """Get the mappings to external registries, if available."""
    entry = get(prefix)
    if entry is None:
        return None
    rv = {}
    for key in read_metaregistry():
        if key not in entry:
            continue
        if key != 'wikidata':
            rv[key] = entry[key]['prefix']
        else:
            value = entry[key].get('property')
            if value is not None:
                rv['wikidata'] = value
    return rv


def get_synonyms(prefix: str) -> Optional[Set[str]]:
    """Get the synonyms for a given prefix, if available."""
    entry = get(prefix)
    if entry is None:
        return None
    # TODO aggregate even more from xrefs
    return entry.get('synonyms')


def _get_prefix_key(prefix: str, key: str, sources: Sequence[str]):
    entry = get(prefix)
    if entry is None:
        return None
    rv = entry.get(key)
    if rv is not None:
        return rv
    for source in sources:
        rv = entry.get(source, {}).get(key)
        if rv is not None:
            return rv
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
    return _get_prefix_key(prefix, 'pattern', ('miriam', 'wikidata'))


@lru_cache()
def get_pattern_re(prefix: str):
    """Get the compiled pattern for the given prefix, if it's available."""
    pattern = get_pattern(prefix)
    if pattern is None:
        return None
    return re.compile(pattern)


def namespace_in_lui(prefix: str) -> Optional[bool]:
    """Check if the namespace should appear in the LUI."""
    return _get_prefix_key(prefix, 'namespaceEmbeddedInLui', ('miriam',))


def get_identifiers_org_prefix(prefix: str) -> Optional[str]:
    """Get the identifiers.org prefix if available."""
    return _get_mapped_prefix(prefix, 'miriam')


def get_n2t_prefix(prefix: str) -> Optional[str]:
    """Get the name-to-thing prefix if available."""
    return _get_mapped_prefix(prefix, 'n2t')


def get_bioportal_prefix(prefix: str) -> Optional[str]:
    """Get the Bioportal prefix if available."""
    return _get_mapped_prefix(prefix, 'bioportal')


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
    example = entry.get('ncbi', {}).get('example')
    if example is not None:
        return example
    return None


def has_terms(prefix: str) -> bool:
    """Check if the prefix is specifically noted to not have terms."""
    entry = get(prefix)
    if entry is None:
        return True
    return not entry.get('no_own_terms', False)


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
    rv = _get_prefix_key(prefix, 'contact', ('obofoundry', 'ols'))
    if rv and not EMAIL_RE.match(rv):
        logger.warning('[%s] invalid email address listed: %s', prefix, rv)
        return None
    return rv


def get_homepage(prefix: str) -> Optional[str]:
    """Return the homepage, if available."""
    return _get_prefix_key(prefix, 'homepage', ('obofoundry', 'ols', 'n2t', 'wikidata', 'go', 'ncbi'))


def get_obo_download(prefix: str) -> Optional[str]:
    """Get the download link for the latest OBO file."""
    entry = get(prefix)
    if entry is None:
        return None
    return entry.get('obofoundry', {}).get('download.obo')


def get_owl_download(prefix: str) -> Optional[str]:
    """Get the download link for the latest OWL file."""
    entry = get(prefix)
    if entry is None:
        return None
    return entry.get('ols', {}).get('version.iri')


def is_provider(prefix: str) -> bool:
    """Get if the prefix is a provider.

    :param prefix: The prefix to look up
    :returns: if the prefix is a provider

    >>> assert not is_provider('pdb')
    >>> assert is_provider('validatordb')
    """
    entry = get(prefix)
    if entry is None:
        return False
    return entry.get('type') == 'provider'


def get_provides_for(prefix: str) -> Optional[str]:
    """Get the resource that the given prefix provides for, or return none if not a provider.

    :param prefix: The prefix to look up
    :returns: The prefix of the resource that the given prefix provides for, if it's a provider

    >>> assert get_provides_for('pdb') is None
    >>> assert 'pdb' == get_provides_for('validatordb')
    """
    entry = get(prefix)
    if entry is None:
        return None
    return entry.get('provides')


def parse_curie(curie: str) -> Union[Tuple[str, str], Tuple[None, None]]:
    """Parse a CURIE, normalizing the prefix and identifier if necessary.

    :param curie: A compact URI (CURIE) in the form of <prefix:identifier>
    :returns: A tuple of the prefix, identifier. If not parsable, returns a tuple of None, None

    Parse canonical CURIE
    >>> parse_curie('go:1234')
    ('go', '1234')

    Normalize prefix
    >>> parse_curie('GO:1234')
    ('go', '1234')

    Address banana problem
    >>> parse_curie('GO:GO:1234')
    ('go', '1234')
    """
    try:
        prefix, identifier = curie.split(':', 1)
    except ValueError:
        return None, None

    # remove redundant prefix
    if identifier.casefold().startswith(f'{prefix.casefold()}:'):
        identifier = identifier[len(prefix) + 1:]

    norm_prefix = normalize_prefix(prefix)
    if not norm_prefix:
        return None, None
    return norm_prefix, identifier


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

    >>> assert 'pubchem.compound' == normalize_prefix('pubchem')

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
                version = datetime.datetime.strptime(version, version_date_fmt).strftime('%Y-%m-%d')
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
            raise ValueError(dedent(f'''\
            [{bioregistry_id}] version "{version}" does not start with prefix "{version_prefix}".
            Update the ["{bioregistry_id}"]["ols_version_prefix"] entry.
            '''))
        version = version[len(version_prefix):]

    if bioregistry_entry.get('ols_version_suffix_split'):
        version = version.split()[0]

    version_suffix = bioregistry_entry.get('ols_version_suffix')
    if version_suffix:
        if not version.endswith(version_suffix):
            raise ValueError(f'[{bioregistry_id}] version {version} does not end with prefix {version_suffix}')
        version = version[:-len(version_suffix)]

    return version
