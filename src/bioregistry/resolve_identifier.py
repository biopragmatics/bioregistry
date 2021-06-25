# -*- coding: utf-8 -*-

"""Resolvers for CURIE (e.g., pairs of prefix and identifier)."""

from typing import Callable, Mapping, Optional, Sequence, Tuple

from .constants import BIOREGISTRY_REMOTE_URL
from .resolve import (
    get, get_banana, get_bioportal_prefix, get_identifiers_org_prefix, get_n2t_prefix,
    get_obofoundry_format, get_ols_prefix, get_pattern_re, namespace_in_lui, normalize_prefix,
)

__all__ = [
    'validate',
    'get_providers',
    'get_providers_list',
    'get_identifiers_org_url',
    'get_identifiers_org_curie',
    'get_obofoundry_format',
    'get_obofoundry_link',
    'get_ols_link',
    'get_bioportal_url',
    'get_n2t_url',
    'get_link',
    'get_registry_resolve_url',
]


def validate(prefix: str, identifier: str) -> Optional[bool]:
    """Validate the identifier against the prefix's pattern, if it exists."""
    pattern = get_pattern_re(prefix)
    if pattern is None:
        return None
    return bool(pattern.match(_get_modified_id(prefix, identifier)))


def _get_modified_id(prefix: str, identifier: str) -> str:
    if not namespace_in_lui(prefix):
        return identifier
    banana = get_banana(prefix)
    if banana:
        if identifier.startswith(f'{banana}:'):
            return identifier
        else:
            return f'{banana}:{identifier}'
    else:
        if identifier.startswith(prefix.upper()):
            return identifier
        else:
            return f'{prefix.upper()}:{identifier}'


def get_default_url(prefix: str, identifier: str) -> Optional[str]:
    """Get the default URL for the given CURIE."""
    entry = get(prefix)
    if entry is None:
        return None
    return entry.get_default_url(identifier)


def get_providers(prefix: str, identifier: str) -> Mapping[str, str]:
    """Get all providers for the CURIE."""
    return dict(get_providers_list(prefix, identifier))


def get_providers_list(prefix: str, identifier: str) -> Sequence[Tuple[str, str]]:
    """Get all providers for the CURIE."""
    rv = []
    for provider, get_url in PROVIDER_FUNCTIONS.items():
        link = get_url(prefix, identifier)
        if link is not None:
            rv.append((provider, link))
    if not rv:
        return rv

    bioregistry_link = _get_bioregistry_link(prefix, identifier)
    if not bioregistry_link:
        return rv

    # if a default URL is available, it goes first. otherwise the bioregistry URL goes first.
    rv.insert(1 if rv[0][0] == 'default' else 0, ('bioregistry', bioregistry_link))
    return rv


def get_identifiers_org_url(prefix: str, identifier: str) -> Optional[str]:
    """Get the identifiers.org URL for the given CURIE."""
    curie = get_identifiers_org_curie(prefix, identifier)
    if curie is None:
        return None
    return f'https://identifiers.org/{curie}'


def get_n2t_url(prefix: str, identifier: str) -> Optional[str]:
    """Get the name-to-thing URL for the given CURIE."""
    n2t_prefix = get_n2t_prefix(prefix)
    if n2t_prefix is None:
        return None
    curie = f'{n2t_prefix}:{identifier}'
    if curie is None:
        return None
    return f'https://n2t.net/{curie}'


def get_bioportal_url(prefix: str, identifier: str) -> Optional[str]:
    """Get the Bioportal URL for the given CURIE.

    :param prefix: The prefix in the CURIE
    :param identifier: The identifier in the CURIE
    :return: A link to the Bioportal page

    >>> get_bioportal_url('chebi', '24431')
    'https://bioportal.bioontology.org/ontologies/CHEBI/?p=classes&conceptid=http://purl.obolibrary.org/obo/CHEBI_24431'
    """
    bioportal_prefix = get_bioportal_prefix(prefix)
    if bioportal_prefix is None:
        return None
    obo_link = get_obofoundry_link(prefix, identifier)
    if obo_link is not None:
        return f'https://bioportal.bioontology.org/ontologies/{bioportal_prefix}/?p=classes&conceptid={obo_link}'
    # TODO there must be other rules?
    return None


# MIRIAM definitions that don't make any sense
MIRIAM_BLACKLIST = {
    # this one uses the names instead of IDs, and points to a dead resource.
    # See https://github.com/identifiers-org/identifiers-org.github.io/issues/139
    'pid.pathway',
}


def get_identifiers_org_curie(prefix: str, identifier: str) -> Optional[str]:
    """Get the identifiers.org CURIE for the given CURIE."""
    miriam_prefix = get_identifiers_org_prefix(prefix)
    if miriam_prefix is None or miriam_prefix in MIRIAM_BLACKLIST:
        return None
    banana = get_banana(prefix)
    if banana:
        if identifier.startswith(f'{banana}:'):
            return identifier
        else:
            return f'{banana}:{identifier}'
    elif namespace_in_lui(prefix):
        if identifier.startswith(prefix.upper()):
            return identifier
        else:
            return f'{prefix.upper()}:{identifier}'
    else:
        return f'{miriam_prefix}:{identifier}'


def get_obofoundry_link(prefix: str, identifier: str) -> Optional[str]:
    """Get the OBO Foundry URL if possible.

    :param prefix: The prefix
    :param identifier: The identifier
    :return: The OBO Foundry URL if the prefix can be mapped to an OBO Foundry entry

    >>> get_obofoundry_link('chebi', '24431')
    'http://purl.obolibrary.org/obo/CHEBI_24431'

    For entries where there's a preferred prefix, it is respected.

    >>> get_obofoundry_link('fbbt', '00007294')
    'http://purl.obolibrary.org/obo/FBbt_00007294'
    """
    fmt = get_obofoundry_format(prefix)
    if fmt is None:
        return None
    return f'{fmt}{identifier}'


def get_ols_link(prefix: str, identifier: str) -> Optional[str]:
    """Get the OLS URL if possible."""
    ols_prefix = get_ols_prefix(prefix)
    obo_link = get_obofoundry_link(prefix, identifier)
    if ols_prefix is None or obo_link is None:
        return None
    return f'https://www.ebi.ac.uk/ols/ontologies/{ols_prefix}/terms?iri={obo_link}'


def _get_bioregistry_link(prefix: str, identifier: str) -> Optional[str]:
    """Get the bioregistry link.

    :param prefix: The prefix in the CURIE
    :param identifier: The identifier in the CURIE
    :return: A link to the bioregistry resolver

    >>> _get_bioregistry_link('chebi', '1234')
    'https://bioregistry.io/chebi:1234'
    """
    norm_prefix = normalize_prefix(prefix)
    if norm_prefix is None:
        return None
    return f'{BIOREGISTRY_REMOTE_URL.rstrip()}/{norm_prefix}:{identifier}'


PROVIDER_FUNCTIONS: Mapping[str, Callable[[str, str], Optional[str]]] = {
    'default': get_default_url,
    'miriam': get_identifiers_org_url,
    'obofoundry': get_obofoundry_link,
    'ols': get_ols_link,
    'n2t': get_n2t_url,
    'bioportal': get_bioportal_url,
}

LINK_PRIORITY = [
    'default',
    'bioregistry',
    'miriam',
    'ols',
    'obofoundry',
    'n2t',
    'bioportal',
]


def get_link(prefix: str, identifier: str, use_bioregistry_io: bool = True) -> Optional[str]:
    """Get the best link for the CURIE, if possible."""
    providers = get_providers(prefix, identifier)
    for key in LINK_PRIORITY:
        if not use_bioregistry_io and key == 'bioregistry':
            continue
        if key not in providers:
            continue
        rv = providers[key]
        if rv is not None:
            return rv
    return None


def get_registry_resolve_url(metaprefix: str, prefix: str, identifier: str) -> Optional[str]:
    """Get the URL to resolve the given prefix/identifier pair with the given resolver."""
    providers = get_providers(prefix, identifier)
    if not providers:
        return None
    return providers.get(metaprefix)
