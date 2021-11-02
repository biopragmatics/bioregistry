# -*- coding: utf-8 -*-

"""API for registries."""

from typing import Optional

from .resolve_identifier import get_providers
from .schema import Registry
from .utils import read_metaregistry

__all__ = [
    "get_registry_uri",
]


def get_registry(metaprefix: str) -> Optional[Registry]:
    """Get the metaregistry entry for the given prefix."""
    return read_metaregistry().get(metaprefix)


def get_registry_name(metaprefix: str) -> Optional[str]:
    """Get the metaregistry name for the given prefix, if it's available."""
    registry = get_registry(metaprefix)
    if registry is None:
        return None
    return registry.name


def get_registry_homepage(metaprefix: str) -> Optional[str]:
    """Get the URL for the registry, if available.

    :param metaprefix: The metaprefix of the registry
    :return: The URL for the registry, if available, otherwise ``None``.

    >>> get_registry_homepage('biolink')
    'https://github.com/biolink/biolink-model'

    ``None`` is returned on missing values.

    >>> get_registry_homepage('missing')
    None
    """
    registry = get_registry(metaprefix)
    if registry is None:
        return None
    return registry.homepage


def get_registry_description(metaprefix: str) -> Optional[str]:
    """Get the description for the registry, if available.

    :param metaprefix: The metaprefix of the registry
    :return: The description for the registry, if available, otherwise ``None``.

    >>> get_registry_description('prefixcommons')
    'A registry of commonly used prefixes in the life sciences and linked data'

    >>> get_registry_description('missing')
    None
    """
    registry = get_registry(metaprefix)
    if registry is None:
        return None
    return registry.description


def get_registry_example(metaprefix: str) -> Optional[str]:
    """Get an example for the registry, if available."""
    registry = get_registry(metaprefix)
    if registry is None:
        return None
    return registry.example


def get_registry_provider_uri_format(metaprefix: str, prefix: str) -> Optional[str]:
    """Get the URL for the resource inside registry, if available."""
    entry = get_registry(metaprefix)
    if entry is None:
        return None
    return entry.get_provider_uri_format(prefix)


def get_registry_uri(metaprefix: str, prefix: str, identifier: str) -> Optional[str]:
    """Get the URL to resolve the given prefix/identifier pair with the given resolver."""
    providers = get_providers(prefix, identifier)
    if not providers:
        return None
    return providers.get(metaprefix)
