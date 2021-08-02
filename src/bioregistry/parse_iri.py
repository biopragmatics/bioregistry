# -*- coding: utf-8 -*-

"""Functionality for parsing IRIs."""

from typing import Tuple, Union

from bioregistry.resolve import get_format_urls

__all__ = [
    'parse_iri',
]

_D = sorted(get_format_urls().items(), key=lambda kv: -len(kv[0]))


def parse_iri(iri: str) -> Union[Tuple[str, str], Tuple[None, None]]:
    """Parse a compact identifier from an IRI.

    :param iri: A valid IRI
    :return: A pair of prefix/identifier, if can be parsed

    IRIs from Identifiers.org (https and http):

    >>> parse_iri("https://identifiers.org/aop.relationships:5")
    ('aop.relationships', '5')
    >>> parse_iri("http://identifiers.org/aop.relationships:5")
    ('aop.relationships', '5')

    IRI from an OBO PURL:

    >>> parse_iri("http://purl.obolibrary.org/obo/DRON_00023232")
    ('dron', '00023232')

    IRI from the OLS:

    >>> parse_iri("https://www.ebi.ac.uk/ols/ontologies/ecao/terms?iri=http://purl.obolibrary.org/obo/ECAO_0107180")
    ('ecao', '0107180')

    IRI from native provider

    >>> parse_iri("https://www.alzforum.org/mutations/1234")
    ('alzforum.mutation', '1234')

    .. todo:: IRI with weird embedding, like ones that end in .html
    """
    for prefix, prefix_url in _D:
        if iri.startswith(prefix_url):
            return prefix, iri[len(prefix_url):]
    return None, None


def _main():
    import bioregistry
    from tabulate import tabulate
    rows = []
    for prefix, resource in bioregistry.read_registry().items():
        example = bioregistry.get_example(prefix)
        if example is None:
            continue
        iri = bioregistry.get_link(prefix, example, use_bioregistry_io=False)
        if iri is None:
            # print('no iri for', prefix, example)
            continue
        k, v = parse_iri(iri)
        rows.append((prefix, example, iri, k, v))
    print(tabulate(rows))


if __name__ == '__main__':
    _main()
