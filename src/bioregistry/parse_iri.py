# -*- coding: utf-8 -*-

"""Functionality for parsing IRIs."""

from typing import Tuple, Union

from .resolve import get_format_urls, parse_curie

__all__ = [
    "parse_iri",
]

#: A prefix map in reverse sorted order based on length of the URL
#: in order to avoid conflicts of sub-URIs (thanks to Nico Matentzoglu for the idea)
PREFIX_MAP = sorted(get_format_urls().items(), key=lambda kv: -len(kv[0]))

OLS_URL_PREFIX = "https://www.ebi.ac.uk/ols/ontologies/"
BIOREGISTRY_PREFIX = "https://bioregistry.io"
OBO_PREFIX = "http://purl.obolibrary.org/obo/"
IDOT_HTTPS_PREFIX = "https://identifiers.org/"
IDOT_HTTP_PREFIX = "http://identifiers.org/"
N2T_PREFIX = "https://n2t.net/"


def parse_iri(iri: str) -> Union[Tuple[str, str], Tuple[None, None]]:
    """Parse a compact identifier from an IRI.

    :param iri: A valid IRI
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

    .. todo:: IRI with weird embedding, like ones that end in .html
    """
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
    for prefix, prefix_url in PREFIX_MAP:
        if iri.startswith(prefix_url):
            return prefix, iri[len(prefix_url) :]
    return None, None


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
    curie = iri[len("http://purl.obolibrary.org/obo/") :]
    return parse_curie(curie, sep="_")


def _main():
    """Run this as ``python -m bioregistry.parse_iri`` to get a list of IRIs that can be constructed, but not parsed."""
    import bioregistry
    from tabulate import tabulate

    rows = []
    for prefix in bioregistry.read_registry():
        example = bioregistry.get_example(prefix)
        if example is None:
            continue
        iri = bioregistry.get_link(prefix, example, use_bioregistry_io=False)
        if iri is None:
            # print('no iri for', prefix, example)
            continue
        k, v = parse_iri(iri)
        if k is None:
            rows.append((prefix, example, iri, k, v))
    print(tabulate(rows))


if __name__ == "__main__":
    _main()
