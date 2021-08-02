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

    >>> parse_iri("https://www.alzforum.org/mutations/1234")
    ('alzforum.mutation', '1234')
    """
    for prefix, prefix_url in _D:
        if iri.startswith(prefix_url):
            return prefix, iri[len(prefix_url):]
    return None, None


def main():
    import bioregistry
    from tabulate import tabulate
    rows=[]
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
    main()
