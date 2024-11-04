# -*- coding: utf-8 -*-

"""Functionality for parsing IRIs."""

from typing import Optional

from .constants import MaybeCURIE
from .resource_manager import manager

__all__ = [
    "curie_from_iri",
    "parse_iri",
]

COMPRESS_ERROR_TEXT = """\
If you provide your own prefix map but want to do compression in bulk,
you should pre-process the prefix map with:

>>> from bioregistry import get_default_converter
>>> from curies import Converter, chain
>>> prefix_map = {"chebi": "https://example.org/chebi:"}
>>> converter = chain([Converter.from_prefix_map(prefix_map), get_default_converter()])
>>> converter.compress("https://example.org/chebi:1234")
'chebi:1234'
""".rstrip()

PARSE_IRI_ERROR_TEXT = """\
If you provide your own prefix map but want to do parsing in bulk,
you should pre-process the prefix map with:

>>> from bioregistry import get_default_converter
>>> from curies import Converter, chain
>>> prefix_map = {"chebi": "https://example.org/chebi:"}
>>> converter = chain([Converter.from_prefix_map(prefix_map), get_default_converter()])
>>> converter.parse_uri("https://example.org/chebi:1234")
('chebi', '1234')
""".rstrip()


def curie_from_iri(
    iri: str,
    *,
    use_preferred: bool = False,
) -> Optional[str]:
    """Generate a CURIE from an IRI via :meth:`Manager.compress`.

    :param iri: A valid IRI
    :param prefix_map:
        This functionality was removed in Bioregistry v0.8.0.
        Leave this as None. This argument will be removed in Bioregistry v0.9.0.
    :param use_preferred:
        If set to true, uses the "preferred prefix", if available, instead
        of the canonicalized Bioregistry prefix.
    :return: A CURIE string, if the IRI can be parsed.
    :raises NotImplementedError: If ``prefix_map`` is not None.
    """
    return manager.compress(iri, use_preferred=use_preferred)


def parse_iri(
    iri: str,
    *,
    use_preferred: bool = False,
) -> MaybeCURIE:
    """Parse a compact identifier from an IRI that wraps :meth:`Manager.parse_uri`.

    :param iri: A valid IRI
    :param use_preferred:
        If set to true, uses the "preferred prefix", if available, instead
        of the canonicalized Bioregistry prefix.
    :return: A pair of prefix/identifier, if can be parsed
    :raises NotImplementedError: If ``prefix_map`` is not None.
    """
    return manager.parse_uri(iri, use_preferred=use_preferred)
