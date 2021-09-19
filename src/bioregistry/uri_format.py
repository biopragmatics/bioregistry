# -*- coding: utf-8 -*-

"""Tools for getting URI format strings.

.. warning::

    URI format strings are different from URI prefix strings. URI format strings have a ``$1`` where
    the prefix should go, which makes them more general than URI prefix strings.
"""

import logging
from typing import Callable, List, Mapping, Optional, Sequence, Tuple

from .resolve import (
    get_default_format,
    get_miriam_format,
    get_obofoundry_formatter,
    get_ols_format,
    get_prefixcommons_format,
    get_resource,
    get_synonyms,
)
from .utils import read_registry

__all__ = [
    "DEFAULT_URI_FORMATTER_PRIORITY",
    "URI_FORMATTERS",
    "get_format",
    "get_format_url",
    "get_format_urls",
    "prepare_prefix_list",
    "get_default_prefix_list",
]

#: The default priority for generating URIs
DEFAULT_URI_FORMATTER_PRIORITY = (
    "bioregistry",
    "obofoundry",
    "prefixcommons",
    "miriam",
    "ols",
)

URI_FORMATTERS: Mapping[str, Callable[[str], Optional[str]]] = {
    "bioregistry": get_default_format,
    "obofoundry": get_obofoundry_formatter,
    "prefixcommons": get_prefixcommons_format,
    "miriam": get_miriam_format,
    "ols": get_ols_format,
}


def get_format(prefix: str, priority: Optional[Sequence[str]] = None) -> Optional[str]:
    """Get the URL format string for the given prefix, if it's available.

    :param prefix: The name of the prefix (possibly unnormalized)
    :param priority: The priority order of metaresources to use for format URL lookup.
        The default is:

        1. Bioregistry
        2. OBO Foundry
        3. Prefix Commons
        4. Identifiers.org / MIRIAM
        5. OLS
    :return: The best URL format string, where the ``$1`` should be replaced by the
        identifier. ``$1`` could potentially appear multiple times.

    >>> import bioregistry
    >>> bioregistry.get_format('chebi')
    'https://www.ebi.ac.uk/chebi/searchId.do?chebiId=CHEBI:$1'

    If you want to specify a different priority order, you can do so with the ``priority`` keyword. This
    is of particular interest to ontologists and semantic web people who might want to use ``purl.obolibrary.org``
    URL prefixes over the URL prefixes corresponding to the first-party providers for each resource (e.g., the
    ChEBI example above). Do so like:

    >>> import bioregistry
    >>> bioregistry.get_format('chebi', priority=['obofoundry', 'bioregistry', 'prefixcommons', 'miriam', 'ols'])
    'http://purl.obolibrary.org/obo/CHEBI_$1'
    """
    entry = get_resource(prefix)
    if entry is None:
        return None
    for metaprefix in priority or DEFAULT_URI_FORMATTER_PRIORITY:
        formatter = URI_FORMATTERS[metaprefix]
        rv = formatter(prefix)
        if rv is not None:
            return rv
    return None


def get_format_url(prefix: str, priority: Optional[Sequence[str]] = None) -> Optional[str]:
    """Get a well-formed format URL for usage in a prefix map.

    :param prefix: The prefix to lookup.
    :param priority: The prioirty order for :func:`get_format`.
    :return: The URL prefix. Similar to what's returned by :func:`bioregistry.get_format`, but
        it MUST have only one ``$1`` and end with ``$1`` to use thie function.

    >>> import bioregistry
    >>> bioregistry.get_format_url('chebi')
    'https://www.ebi.ac.uk/chebi/searchId.do?chebiId=CHEBI:'
    """
    fmt = get_format(prefix, priority=priority)
    if fmt is None:
        logging.debug("term missing formatter: %s", prefix)
        return None
    count = fmt.count("$1")
    if 0 == count:
        logging.debug("formatter missing $1: %s", prefix)
        return None
    if fmt.count("$1") != 1:
        logging.debug("formatter has multiple $1: %s", prefix)
        return None
    if not fmt.endswith("$1"):
        logging.debug("formatter does not end with $1: %s", prefix)
        return None
    return fmt[: -len("$1")]


def get_format_urls(
    *,
    priority: Optional[Sequence[str]] = None,
    include_synonyms: bool = False,
    remapping: Optional[Mapping[str, str]] = None,
) -> Mapping[str, str]:
    """Get a mapping from Bioregistry prefixes to their prefix URLs via :func:`get_format_url`.

    :param priority: A priority list for how to generate prefix URLs.
    :param include_synonyms: Should synonyms of each prefix also be included as additional prefixes, but with
        the same URL prefix?
    :param remapping: A mapping from bioregistry prefixes to preferred prefixes.
    :return: A mapping from prefixes to prefix URLs.
    """
    rv = {}
    for prefix in read_registry():
        prefix_url = get_format_url(prefix, priority=priority)
        if prefix_url is None:
            continue
        rv[prefix] = prefix_url
        if include_synonyms:
            for synonym in get_synonyms(prefix) or []:
                rv[synonym] = prefix_url
    if remapping:
        return {remapping.get(prefix, prefix): prefix_url for prefix, prefix_url in rv.items()}
    return rv


def _sort_key(kv: Tuple[str, str]) -> int:
    """Return a value appropriate for sorting a pair of prefix/IRI."""
    return -len(kv[0])


def prepare_prefix_list(prefix_map: Mapping[str, str]) -> List[Tuple[str, str]]:
    """Prepare a priority prefix list from a prefix map."""
    return sorted(prefix_map.items(), key=_sort_key)


def get_default_prefix_list() -> List[Tuple[str, str]]:
    """Get the default priority prefix list."""
    #: A prefix map in reverse sorted order based on length of the URL
    #: in order to avoid conflicts of sub-URIs (thanks to Nico Matentzoglu for the idea)
    return prepare_prefix_list(get_format_urls())
