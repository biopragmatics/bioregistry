# -*- coding: utf-8 -*-

"""Functionality for parsing IRIs."""

from typing import List, Mapping, Optional, Tuple, Union

from .resolve import get_preferred_prefix, parse_curie
from .resource_manager import manager
from .utils import curie_to_str

__all__ = [
    "curie_from_iri",
    "parse_iri",
    "parse_obolibrary_purl",
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
    :raises NotImplementedError: If prefix map is given

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

    Corner cases:

    >>> parse_iri("https://omim.org/MIM:PS214100")
    ('omim.ps', '214100')

    .. todo:: IRI with weird embedding, like ones that end in .html
    """
    if prefix_map is None:
        return manager.parse_uri(iri)

    raise NotImplementedError(
        "Parsing without a pre-compiled `curies.Converter` class is very slow. "
        "This functionality has been removed from the Bioregistry in the 0.7.0 release.",
    )


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
