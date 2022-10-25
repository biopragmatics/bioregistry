# -*- coding: utf-8 -*-

"""Functionality for parsing IRIs."""

import warnings
from functools import lru_cache
from typing import List, Mapping, Optional, Tuple, Union

import curies

from .resolve import get_preferred_prefix, parse_curie
from .resource_manager import manager, prepare_prefix_list
from .uri_format import get_prefix_map
from .utils import curie_to_str

__all__ = [
    "curie_from_iri",
    "parse_iri",
    "parse_obolibrary_purl",
    "ensure_prefix_list",
]

OLS_URL_PREFIX = "https://www.ebi.ac.uk/ols/ontologies/"
BIOREGISTRY_PREFIX = "https://bioregistry.io"
OBO_PREFIX = "http://purl.obolibrary.org/obo/"
IDOT_HTTPS_PREFIX = "https://identifiers.org/"
IDOT_HTTP_PREFIX = "http://identifiers.org/"
N2T_PREFIX = "https://n2t.net/"

PrefixList = List[Tuple[str, str]]


def curie_from_iri(
    iri: str,
    *,
    prefix_map: Union[Mapping[str, str], PrefixList, None] = None,
    use_preferred: bool = False,
) -> Optional[str]:
    """Parse a compact identifier from an IRI using :func:`parse_iri` and reconstitute it.

    :param iri: A valid IRI
    :param prefix_map: See :func:`parse_iri`
    :param use_preferred: Should the preferred prefix be used instead
        of the Bioregistry prefix (if it exists)?
    :return: A CURIE string, if the IRI can be parsed by :func:`parse_iri`.

    IRI from an OBO PURL:

    >>> curie_from_iri("http://purl.obolibrary.org/obo/DRON_00023232")
    'dron:00023232'

    IRI from the OLS:

    >>> curie_from_iri("https://www.ebi.ac.uk/ols/ontologies/ecao/terms?iri=http://purl.obolibrary.org/obo/ECAO_1")
    'ecao:1'

    .. todo:: IRI from bioportal

    IRI from native provider

    >>> curie_from_iri("https://www.alzforum.org/mutations/1234")
    'alzforum.mutation:1234'

    Dog food:

    >>> curie_from_iri("https://bioregistry.io/DRON:00023232")
    'dron:00023232'

    IRIs from Identifiers.org (https and http, colon and slash):

    >>> curie_from_iri("https://identifiers.org/aop.relationships:5")
    'aop.relationships:5'
    >>> curie_from_iri("http://identifiers.org/aop.relationships:5")
    'aop.relationships:5'
    >>> curie_from_iri("https://identifiers.org/aop.relationships/5")
    'aop.relationships:5'
    >>> curie_from_iri("http://identifiers.org/aop.relationships/5")
    'aop.relationships:5'

    IRI from N2T
    >>> curie_from_iri("https://n2t.net/aop.relationships:5")
    'aop.relationships:5'

    IRI from an OBO PURL (with preferred prefix)
    >>> curie_from_iri("http://purl.obolibrary.org/obo/DRON_00023232", use_preferred=True)
    'DRON:00023232'
    """
    prefix, identifier = parse_iri(iri=iri, prefix_map=prefix_map)
    if prefix is None or identifier is None:
        return None
    if use_preferred:
        prefix = get_preferred_prefix(prefix) or prefix
    return curie_to_str(prefix, identifier)


@lru_cache(1)
def _get_converter() -> curies.Converter:
    return manager.get_converter()


def parse_iri(
    iri: str,
    *,
    prefix_map: Union[Mapping[str, str], PrefixList, None] = None,
) -> Union[Tuple[str, str], Tuple[None, None]]:
    """Parse a compact identifier from an IRI.

    :param iri: A valid IRI
    :param prefix_map:
        If None, will use the default prefix map. If a mapping, will convert into a sorted
        list using :func:`ensure_prefix_list`. If you plan
        to use this function in a loop, pre-compute this and pass it instead.
        If a list of pairs is passed, will use it directly.
    :return: A pair of prefix/identifier, if can be parsed

    IRI from an OBO PURL:

    >>> parse_iri("http://purl.obolibrary.org/obo/DRON_00023232")
    ('dron', '00023232')

    IRI from the OLS:

    >>> parse_iri("https://www.ebi.ac.uk/ols/ontologies/ecao/terms?iri=http://purl.obolibrary.org/obo/ECAO_0107180")
    ('ecao', '0107180')

    .. todo:: IRI from bioportal

    IRI from native provider

    >>> parse_iri("https://www.alzforum.org/mutations/1234")
    ('alzforum.mutation', '1234')

    Dog food:

    >>> parse_iri("https://bioregistry.io/DRON:00023232")
    ('dron', '00023232')

    IRIs from Identifiers.org (https and http, colon and slash):

    >>> parse_iri("https://identifiers.org/aop.relationships:5")
    ('aop.relationships', '5')
    >>> parse_iri("http://identifiers.org/aop.relationships:5")
    ('aop.relationships', '5')
    >>> parse_iri("https://identifiers.org/aop.relationships/5")
    ('aop.relationships', '5')
    >>> parse_iri("http://identifiers.org/aop.relationships/5")
    ('aop.relationships', '5')

    IRI from N2T
    >>> parse_iri("https://n2t.net/aop.relationships:5")
    ('aop.relationships', '5')

    Handle either HTTP or HTTPS:
    >>> parse_iri("http://braininfo.rprc.washington.edu/centraldirectory.aspx?ID=268")
    ('neuronames', '268')
    >>> parse_iri("https://braininfo.rprc.washington.edu/centraldirectory.aspx?ID=268")
    ('neuronames', '268')

    Provide your own prefix map for one-off parsing (i.e., not in bulk):
    >>> prefix_map = {"chebi": "https://example.org/chebi:"}
    >>> parse_iri("https://example.org/chebi:1234", prefix_map=prefix_map)
    ('chebi', '1234')

    If you provide your own prefix map but want to do parsing in bulk,
    you should pre-process the prefix map with:

    >>> from bioregistry import ensure_prefix_list
    >>> prefix_map = {"chebi": "https://example.org/chebi:"}
    >>> prefix_list = ensure_prefix_list(prefix_map)
    >>> parse_iri("https://example.org/chebi:1234", prefix_map=prefix_list)
    ('chebi', '1234')

    Corner cases:

    >>> parse_iri("https://omim.org/MIM:PS214100")
    ('omim.ps', '214100')

    .. todo:: IRI with weird embedding, like ones that end in .html
    """
    if prefix_map is None:
        return _get_converter().parse_uri(iri)

    warnings.warn(
        "Parsing without a pre-compiled `curies.Converter` class is very slow. "
        "This functionality will be removed from the Bioregistry in a future version.",
    )
    # TODO remove this and update all relevant docstrings and README
    if isinstance(prefix_map, list):
        return _parse_iri(iri, prefix_map)
    prefix_list = ensure_prefix_list(prefix_map)
    return _parse_iri(iri, prefix_list)


def _parse_iri(iri: str, prefix_list: List[Tuple[str, str]]):
    if iri.startswith(BIOREGISTRY_PREFIX):
        curie = iri[len(BIOREGISTRY_PREFIX) :]
        return parse_curie(curie)
    if iri.startswith(OLS_URL_PREFIX):
        sub_iri = iri.rsplit("=", 1)[1]
        return parse_obolibrary_purl(sub_iri)
    if iri.startswith(OBO_PREFIX):
        return parse_obolibrary_purl(iri)
    if iri.startswith(IDOT_HTTPS_PREFIX):
        curie = iri[len(IDOT_HTTPS_PREFIX) :]
        return _safe_parse_curie(curie)
    if iri.startswith(IDOT_HTTP_PREFIX):
        curie = iri[len(IDOT_HTTP_PREFIX) :]
        return _safe_parse_curie(curie)
    if iri.startswith(N2T_PREFIX):
        curie = iri[len(N2T_PREFIX) :]
        return parse_curie(curie)
    for prefix, prefix_url in prefix_list:
        if iri.startswith(prefix_url):
            return prefix, iri[len(prefix_url) :]
    return None, None


def ensure_prefix_list(
    prefix_map: Optional[Mapping[str, str]] = None, **kwargs
) -> List[Tuple[str, str]]:
    """Ensure a prefix list, using the given merge strategy with default."""
    _prefix_map = dict(get_prefix_map(**kwargs))
    if prefix_map:
        _prefix_map.update(prefix_map)
    return prepare_prefix_list(_prefix_map)


def _safe_parse_curie(curie: str) -> Union[Tuple[str, str], Tuple[None, None]]:
    for sep in "_/:":
        prefix, identifier = parse_curie(curie, sep)
        if prefix is not None and identifier is not None:
            return prefix, identifier
    return None, None


def parse_obolibrary_purl(iri: str) -> Union[Tuple[str, str], Tuple[None, None]]:
    """Parse an OBO Library PURL.

    :param iri: A valid IRI
    :return: A pair of prefix/identifier, if can be parsed

    >>> parse_obolibrary_purl("http://purl.obolibrary.org/obo/DRON_00023232")
    ('dron', '00023232')

    >>> parse_obolibrary_purl("http://purl.obolibrary.org/obo/FBbt_0000001")
    ('fbbt', '0000001')
    """
    curie = iri[len(OBO_PREFIX) :]
    return parse_curie(curie, sep="_")
