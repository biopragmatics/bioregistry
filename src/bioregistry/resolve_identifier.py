# -*- coding: utf-8 -*-

"""Resolvers for CURIE (e.g., pairs of prefix and identifier)."""

from typing import Callable, Mapping, Optional

from .resolve import (
    get, get_banana, get_identifiers_org_prefix, get_obofoundry_prefix, get_ols_prefix, get_pattern_re,
    namespace_in_lui,
)

__all__ = [
    'validate',
    'get_providers',
    'get_identifiers_org_url',
    'get_identifiers_org_curie',
    'get_obofoundry_link',
    'get_ols_link',
    'get_link',
]


def validate(prefix: str, identifier: str) -> Optional[bool]:
    """Validate the identifier against the prefix's pattern, if it exists."""
    pattern = get_pattern_re(prefix)
    if pattern is None:
        return None

    if namespace_in_lui(prefix) and not identifier.startswith(f'{prefix.upper()}:'):
        # Some cases do not use uppercase
        identifier = f'{prefix.upper()}:{identifier}'

    return bool(pattern.match(identifier))


def get_default_url(prefix: str, identifier: str) -> Optional[str]:
    """Get the default URL for the given CURIE."""
    entry = get(prefix)
    if entry is None:
        return None
    url = entry.get('url')
    if url is None:
        return None
    return url.replace('$1', identifier)


def get_providers(prefix: str, identifier: str) -> Mapping[str, str]:
    """Get all providers for the CURIE."""
    rv = {}
    for provider, get_url in PROVIDER_FUNCTIONS.items():
        link = get_url(prefix, identifier)
        if link is not None:
            rv[provider] = link
    return rv


def get_identifiers_org_url(prefix: str, identifier: str) -> Optional[str]:
    """Get the identifiers.org URL for the given CURIE."""
    curie = get_identifiers_org_curie(prefix, identifier)
    if curie is None:
        return None
    return f'https://identifiers.org/{curie}'


def get_identifiers_org_curie(prefix: str, identifier: str) -> Optional[str]:
    """Get the identifiers.org CURIE for the given CURIE."""
    miriam_prefix = get_identifiers_org_prefix(prefix)
    if miriam_prefix is None:
        return None
    if not namespace_in_lui(prefix):
        return f'{prefix}:{identifier}'
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


def get_obofoundry_link(prefix: str, identifier: str) -> Optional[str]:
    """Get the OBO Foundry URL if possible."""
    obo_prefix = get_obofoundry_prefix(prefix)
    if obo_prefix is None:
        return None
    return f'http://purl.obolibrary.org/obo/{obo_prefix.upper()}_{identifier}'


def get_ols_link(prefix: str, identifier: str) -> Optional[str]:
    """Get the OLS URL if possible."""
    ols_prefix = get_ols_prefix(prefix)
    obo_link = get_obofoundry_link(prefix, identifier)
    if ols_prefix is None or obo_link is None:
        return None
    return f'https://www.ebi.ac.uk/ols/ontologies/{ols_prefix}/terms?iri={obo_link}'


PROVIDER_FUNCTIONS: Mapping[str, Callable[[str, str], Optional[str]]] = {
    'default': get_default_url,
    'miriam': get_identifiers_org_url,
    'obofoundry': get_obofoundry_link,
    'ols': get_ols_link,
}

LINK_PRIORITY = [
    'default',
    'miriam',
    'ols',
    'obofoundry',
]


def get_link(prefix: str, identifier: str) -> Optional[str]:
    """Get the best link for the CURIE, if possible."""
    providers = get_providers(prefix, identifier)
    for key in LINK_PRIORITY:
        if key not in providers:
            continue
        rv = providers[key]
        if rv is not None:
            return rv
    return None
