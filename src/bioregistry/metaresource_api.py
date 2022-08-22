# -*- coding: utf-8 -*-

"""API for registries."""

from typing import Optional

from .resource_manager import manager
from .schema import Registry

__all__ = [
    "get_registry",
    "get_registry_name",
    "get_registry_short_name",
    "get_registry_homepage",
    "get_registry_description",
    "get_registry_example",
    "get_registry_provider_uri_format",
    "get_registry_uri",
]


def get_registry(metaprefix: str) -> Optional[Registry]:
    """Get the metaregistry entry for the given prefix."""
    return manager.get_registry(metaprefix)


def get_registry_name(metaprefix: str) -> Optional[str]:
    """Get the metaregistry name for the given prefix, if it's available."""
    return manager.get_registry_name(metaprefix)


def get_registry_short_name(metaprefix: str) -> Optional[str]:
    """Get the metaregistry short name for the given prefix, if it's available."""
    registry = get_registry(metaprefix)
    if registry is None:
        return None
    return registry.get_short_name()


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
    return manager.get_registry_homepage(metaprefix)


def get_registry_description(metaprefix: str) -> Optional[str]:
    """Get the description for the registry, if available.

    :param metaprefix: The metaprefix of the registry
    :return: The description for the registry, if available, otherwise ``None``.

    >>> get_registry_description('biocontext')
    'BioContext contains modular JSON-LD contexts for bioinformatics data.'

    >>> get_registry_description('missing')
    None
    """
    return manager.get_registry_description(metaprefix)


def get_registry_example(metaprefix: str) -> Optional[str]:
    """Get an example for the registry, if available."""
    registry = get_registry(metaprefix)
    if registry is None:
        return None
    return registry.example


def get_registry_provider_uri_format(metaprefix: str, prefix: str) -> Optional[str]:
    """Get the URL for the resource inside registry, if available."""
    return manager.get_registry_provider_uri_format(metaprefix, prefix)


def get_registry_uri(metaprefix: str, prefix: str, identifier: str) -> Optional[str]:
    """Get the URL to resolve the given prefix/identifier pair with the given resolver."""
    return manager.get_registry_uri(metaprefix, prefix, identifier)
