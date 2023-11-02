# -*- coding: utf-8 -*-

"""Tools for getting URI format strings.

.. warning::

    URI format strings are different from URI prefix strings. URI format strings have a ``$1`` where
    the prefix should go, which makes them more general than URI prefix strings.
"""

from typing import Collection, Mapping, Optional, Sequence

from .resource_manager import manager

__all__ = [
    "get_uri_format",
    "get_uri_prefix",
    "get_prefix_map",
    "get_pattern_map",
]


def get_uri_format(prefix: str, priority: Optional[Sequence[str]] = None) -> Optional[str]:
    """Get the URI format string for the given prefix, if it's available.

    :param prefix: The name of the prefix (possibly unnormalized)
    :param priority: The priority order of metaresources to use for URI format string lookup.
        The default is:

        1. Default first party (from the Bioregistry, BioContext, or MIRIAM)
        2. OBO Foundry
        3. BioContext
        4. MIRIAM/Identifiers.org
        5. N2T
        6. OLS
        7. Prefix Commons

    :return: The best URI format string, where the ``$1`` should be replaced by the
        identifier. ``$1`` could potentially appear multiple times.

    >>> import bioregistry
    >>> bioregistry.get_uri_format('chebi')
    'http://purl.obolibrary.org/obo/CHEBI_$1'

    If you want to specify a different priority order, you can do so with the ``priority`` keyword. This
    is of particular interest to ontologists and semantic web people who might want to use ``purl.obolibrary.org``
    URI prefixes over the URI prefixes corresponding to the first-party providers for each resource (e.g., the
    ChEBI example above). Do so like:

    >>> import bioregistry
    >>> bioregistry.get_uri_format('chebi', priority=['obofoundry', 'bioregistry', 'biocontext', 'miriam', 'ols'])
    'http://purl.obolibrary.org/obo/CHEBI_$1'
    """
    return manager.get_uri_format(prefix=prefix, priority=priority)


def get_uri_prefix(prefix: str, priority: Optional[Sequence[str]] = None) -> Optional[str]:
    """Get a well-formed URI prefix for usage in a prefix map.

    :param prefix: The prefix to lookup.
    :param priority: The prioirty order for :func:`get_format`.
    :return: The URI prefix. Similar to what's returned by :func:`bioregistry.get_format`, but
        it MUST have only one ``$1`` and end with ``$1`` to use thie function.

    >>> import bioregistry
    >>> bioregistry.get_uri_prefix('chebi')
    'http://purl.obolibrary.org/obo/CHEBI_'
    """
    return manager.get_uri_prefix(prefix=prefix, priority=priority)


def get_prefix_map(
    *,
    prefix_priority: Optional[Sequence[str]] = None,
    uri_prefix_priority: Optional[Sequence[str]] = None,
    include_synonyms: bool = False,
    remapping: Optional[Mapping[str, str]] = None,
    blacklist: Optional[Collection[str]] = None,
) -> Mapping[str, str]:
    """Get a mapping from Bioregistry prefixes to their URI prefixes.

    :param prefix_priority:
        The order of metaprefixes OR "preferred" for choosing a primary prefix
        OR "default" for Bioregistry prefixes
    :param uri_prefix_priority:
        The order of metaprefixes for choosing the primary URI prefix OR
        "default" for Bioregistry prefixes
    :param include_synonyms: Should synonyms of each prefix also be included as additional prefixes, but with
        the same URI prefix?
    :param remapping: A mapping from bioregistry prefixes to preferred prefixes.
    :param blacklist: Prefixes to skip
    :return: A mapping from prefixes to URI prefixes.
    """
    return manager.get_prefix_map(
        prefix_priority=prefix_priority,
        uri_prefix_priority=uri_prefix_priority,
        include_synonyms=include_synonyms,
        remapping=remapping,
        blacklist=blacklist,
    )


def get_pattern_map(
    *,
    include_synonyms: bool = False,
    remapping: Optional[Mapping[str, str]] = None,
    blacklist: Optional[Collection] = None,
) -> Mapping[str, str]:
    """Get a mapping from Bioregistry prefixes to their regular expression patterns.

    :param include_synonyms: Should synonyms of each prefix also be included as additional prefixes, but with
        the same URI prefix?
    :param remapping: A mapping from bioregistry prefixes to preferred prefixes.
    :param blacklist: Prefixes to skip
    :return: A mapping from prefixes to regular expression pattern strings.
    """
    return manager.get_pattern_map(
        include_synonyms=include_synonyms,
        remapping=remapping,
        blacklist=blacklist,
    )
