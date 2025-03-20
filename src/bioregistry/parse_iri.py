"""Functionality for parsing IRIs."""

from __future__ import annotations

from typing import Literal, Optional, overload

from curies import ReferenceTuple

from .constants import FailureReturnType
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
    :param use_preferred:
        If set to true, uses the "preferred prefix", if available, instead
        of the canonicalized Bioregistry prefix.
    :return: A CURIE string, if the IRI can be parsed.
    """
    return manager.compress(iri, use_preferred=use_preferred)


# docstr-coverage:excused `overload`
@overload
def parse_iri(
    iri: str,
    *,
    use_preferred: bool = ...,
    on_failure_return_type: Literal[FailureReturnType.pair] = FailureReturnType.pair,
) -> ReferenceTuple | tuple[None, None]: ...


# docstr-coverage:excused `overload`
@overload
def parse_iri(
    iri: str,
    *,
    use_preferred: bool = ...,
    on_failure_return_type: Literal[FailureReturnType.single],
) -> ReferenceTuple | None: ...


def parse_iri(
    iri: str,
    *,
    use_preferred: bool = False,
    on_failure_return_type: FailureReturnType = FailureReturnType.pair,
) -> ReferenceTuple | tuple[None, None] | None:
    """Parse a compact identifier from an IRI that wraps :meth:`Manager.parse_uri`.

    :param iri: A valid IRI
    :param use_preferred:
        If set to true, uses the "preferred prefix", if available, instead
        of the canonicalized Bioregistry prefix.
    :param on_failure_return_type: whether to return a single None or a pair of None's
    :return: A pair of prefix/identifier, if can be parsed
    :raises TypeError: if an invalid on_failure_return_type is given
    """
    if on_failure_return_type == FailureReturnType.single:
        return manager.parse_uri(
            iri, use_preferred=use_preferred, on_failure_return_type=on_failure_return_type
        )
    elif on_failure_return_type == FailureReturnType.pair:
        return manager.parse_uri(
            iri, use_preferred=use_preferred, on_failure_return_type=on_failure_return_type
        )
    else:
        raise TypeError
