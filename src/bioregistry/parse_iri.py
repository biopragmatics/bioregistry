"""Functionality for parsing IRIs."""

from __future__ import annotations

from typing import Literal, overload

import curies
from curies import ReferenceTuple

from .constants import FailureReturnType, MaybeCURIE, NonePair, get_failure_return_type
from .resource_manager import manager

__all__ = [
    "curie_from_iri",
    "get_default_converter",
    "normalize_curie",
    "normalize_parsed_curie",
    "normalize_prefix",
    "parse_curie",
    "parse_iri",
]


def get_default_converter() -> curies.Converter:
    """Get a converter from this manager."""
    return manager.converter


def curie_from_iri(
    iri: str,
    *,
    use_preferred: bool = False,
) -> str | None:
    """Generate a CURIE from an IRI via :meth:`Manager.compress`.

    :param iri: A valid IRI
    :param use_preferred: If set to true, uses the "preferred prefix", if available,
        instead of the canonicalized Bioregistry prefix.

    :returns: A CURIE string, if the IRI can be parsed.
    """
    rv = parse_iri(
        iri, use_preferred=use_preferred, on_failure_return_type=FailureReturnType.single
    )
    if rv:
        return rv.curie
    return None


# docstr-coverage:excused `overload`
@overload
def parse_iri(
    iri: str,
    *,
    use_preferred: bool = ...,
    on_failure_return_type: Literal[FailureReturnType.pair] = FailureReturnType.pair,
) -> ReferenceTuple | NonePair: ...


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
) -> ReferenceTuple | NonePair | None:
    """Parse a compact identifier from an IRI that wraps :meth:`Manager.parse_uri`.

    :param iri: A valid IRI
    :param use_preferred: If set to true, uses the "preferred prefix", if available,
        instead of the canonicalized Bioregistry prefix.
    :param on_failure_return_type: whether to return a single None or a pair of None's

    :returns: A pair of prefix/identifier, if can be parsed

    :raises TypeError: if an invalid on_failure_return_type is given
    """
    rv = get_default_converter().parse_uri(iri, return_none=True)
    if rv is None:
        return get_failure_return_type(on_failure_return_type)
    # don't invoke the manager until it's needed
    if not use_preferred:
        return rv
    return manager.make_preferred(rv, use_preferred=True)


# docstr-coverage:excused `overload`
@overload
def normalize_curie(
    curie: str,
    *,
    sep: str = ...,
    use_preferred: bool = ...,
    strict: Literal[True] = True,
) -> str: ...


# docstr-coverage:excused `overload`
@overload
def normalize_curie(
    curie: str,
    *,
    sep: str = ...,
    use_preferred: bool = ...,
    strict: Literal[False] = False,
) -> str | None: ...


def normalize_curie(
    curie: str,
    *,
    sep: str = ":",
    use_preferred: bool = False,
    strict: bool = False,
) -> str | None:
    """Normalize a CURIE.

    :param curie: A compact URI (CURIE) in the form of <prefix:identifier>
    :param sep: The separator for the CURIE. Defaults to the colon ":" however the slash
        "/" is sometimes used in Identifiers.org and the underscore "_" is used for OBO PURLs.
    :param use_preferred:
        If set to true, uses the "preferred prefix", if available, instead
        of the canonicalized Bioregistry prefix.
    :param strict: If true, raises an error if the prefix can't be standardized
    :return: A normalized CURIE, if possible using the colon as a separator

    >>> normalize_curie("pdb:1234")
    'pdb:1234'

    Fix commonly mistaken prefix
    >>> normalize_curie("pubchem:1234")
    'pubchem.compound:1234'

    Address banana problem
    >>> normalize_curie("GO:GO:1234")
    'go:1234'
    >>> normalize_curie("go:GO:1234")
    'go:1234'
    >>> normalize_curie("go:go:1234")
    'go:1234'
    >>> normalize_curie("go:1234")
    'go:1234'

    Address banana problem with OBO banana
    >>> normalize_curie("fbbt:FBbt:1234")
    'fbbt:1234'
    >>> normalize_curie("fbbt:fbbt:1234")
    'fbbt:1234'
    >>> normalize_curie("fbbt:1234")
    'fbbt:1234'

    Address banana problem with explit banana
    >>> normalize_curie("go.ref:GO_REF:1234")
    'go.ref:1234'
    >>> normalize_curie("go.ref:1234")
    'go.ref:1234'

    Parse OBO PURL curies
    >>> normalize_curie("GO_1234", sep="_")
    'go:1234'

    Use preferred
    >>> normalize_curie("GO_1234", sep="_", use_preferred=True)
    'GO:1234'
    """
    if strict:
        return manager.normalize_curie(curie, sep=sep, use_preferred=use_preferred, strict=True)
    return manager.normalize_curie(curie, sep=sep, use_preferred=use_preferred, strict=False)


# docstr-coverage:excused `overload`
@overload
def normalize_parsed_curie(
    prefix: str,
    identifier: str,
    *,
    use_preferred: bool = ...,
    strict: Literal[True] = True,
) -> ReferenceTuple: ...


# docstr-coverage:excused `overload`
@overload
def normalize_parsed_curie(
    prefix: str,
    identifier: str,
    *,
    use_preferred: bool = ...,
    strict: Literal[False] = False,
) -> ReferenceTuple | NonePair: ...


def normalize_parsed_curie(
    prefix: str,
    identifier: str,
    *,
    use_preferred: bool = False,
    strict: bool = False,
) -> ReferenceTuple | NonePair:
    """Normalize a prefix/identifier pair.

    :param prefix: The prefix in the CURIE
    :param identifier: The identifier in the CURIE
    :param use_preferred:
        If set to true, uses the "preferred prefix", if available, instead
        of the canonicalized Bioregistry prefix.
    :param strict: If true, raises an error if the prefix can't be standardized
    :return: A normalized prefix/identifier pair, conforming to Bioregistry standards. This means no redundant
        prefixes or bananas, all lowercase.
    """
    if strict:
        return manager.normalize_parsed_curie(
            prefix,
            identifier,
            use_preferred=use_preferred,
            strict=strict,
        )
    return manager.normalize_parsed_curie(
        prefix,
        identifier,
        use_preferred=use_preferred,
        on_failure_return_type=FailureReturnType.pair,
        strict=strict,
    )


# docstr-coverage:excused `overload`
@overload
def normalize_prefix(
    prefix: str, *, use_preferred: bool = False, strict: Literal[True] = True
) -> str: ...


# docstr-coverage:excused `overload`
@overload
def normalize_prefix(
    prefix: str, *, use_preferred: bool = False, strict: Literal[False] = False
) -> str | None: ...


def normalize_prefix(
    prefix: str, *, use_preferred: bool = False, strict: bool = False
) -> str | None:
    """Get the normalized prefix, or return None if not registered.

    :param prefix: The prefix to normalize, which could come from Bioregistry,
        OBO Foundry, OLS, or any of the curated synonyms in the Bioregistry
    :param strict: If true and the prefix could not be looked up, raises an error
    :param use_preferred:
        If set to true, uses the "preferred prefix", if available, instead
        of the canonicalized Bioregistry prefix.
    :returns: The canonical Bioregistry prefix, it could be looked up. This
        will usually take precedence: MIRIAM, OBO Foundry / OLS, Custom except
        in a few cases, such as NCBITaxon.

    This works for synonym prefixes, like:

    >>> assert "ncbitaxon" == normalize_prefix("taxonomy")

    This works for common mistaken prefixes, like:

    >>> assert "pubchem.compound" == normalize_prefix("pubchem")

    This works for prefixes that are often written many ways, like:

    >>> assert "ec" == normalize_prefix("ec-code")
    >>> assert "ec" == normalize_prefix("EC_CODE")

    Get a "preferred" prefix:

    >>> normalize_prefix("go", use_preferred=True)
    'GO'
    """
    if strict:
        return manager.normalize_prefix(prefix, use_preferred=use_preferred, strict=True)
    return manager.normalize_prefix(prefix, use_preferred=use_preferred, strict=False)


# docstr-coverage:excused `overload`
@overload
def parse_curie(
    curie: str,
    *,
    sep: str = ...,
    use_preferred: bool = ...,
    on_failure_return_type: FailureReturnType = ...,
    strict: Literal[True] = True,
) -> ReferenceTuple: ...


# docstr-coverage:excused `overload`
@overload
def parse_curie(
    curie: str,
    *,
    sep: str = ...,
    use_preferred: bool = ...,
    on_failure_return_type: Literal[FailureReturnType.single],
    strict: Literal[False] = False,
) -> ReferenceTuple | None: ...


# docstr-coverage:excused `overload`
@overload
def parse_curie(
    curie: str,
    *,
    sep: str = ...,
    use_preferred: bool = ...,
    on_failure_return_type: Literal[FailureReturnType.pair] = FailureReturnType.pair,
    strict: Literal[False] = False,
) -> ReferenceTuple | NonePair: ...


def parse_curie(
    curie: str,
    *,
    sep: str = ":",
    use_preferred: bool = False,
    on_failure_return_type: FailureReturnType = FailureReturnType.pair,
    strict: bool = False,
) -> MaybeCURIE:
    """Parse a CURIE, normalizing the prefix and identifier if necessary.

    :param curie: A compact URI (CURIE) in the form of <prefix:identifier>
    :param sep:
        The separator for the CURIE. Defaults to the colon ":" however the slash
        "/" is sometimes used in Identifiers.org and the underscore "_" is used for OBO PURLs.
    :param use_preferred:
        If set to true, uses the "preferred prefix", if available, instead
        of the canonicalized Bioregistry prefix.
    :param on_failure_return_type: whether to return a single None or a pair of None's
    :returns: A tuple of the prefix, identifier, if parsable
    :raises TypeError: If an invalid on_failure_return_type is given

    The algorithm for parsing a CURIE is very simple: it splits the string on the leftmost occurrence
    of the separator (usually a colon ":" unless specified otherwise). The left part is the prefix,
    and the right part is the identifier.

    >>> parse_curie("pdb:1234")
    ReferenceTuple('pdb', '1234')

    Address banana problem
    >>> parse_curie("go:GO:1234")
    ReferenceTuple('go', '1234')
    >>> parse_curie("go:go:1234")
    ReferenceTuple('go', '1234')
    >>> parse_curie("go:1234")
    ReferenceTuple('go', '1234')

    Address banana problem with OBO banana
    >>> parse_curie("fbbt:FBbt:1234")
    ReferenceTuple('fbbt', '1234')
    >>> parse_curie("fbbt:fbbt:1234")
    ReferenceTuple('fbbt', '1234')
    >>> parse_curie("fbbt:1234")
    ReferenceTuple('fbbt', '1234')

    Address banana problem with explit banana
    >>> parse_curie("go.ref:GO_REF:1234")
    ReferenceTuple('go.ref', '1234')
    >>> parse_curie("go.ref:1234")
    ReferenceTuple('go.ref', '1234')

    Parse OBO PURL curies
    >>> parse_curie("GO_1234", sep="_")
    ReferenceTuple('go', '1234')

    Banana with no peel:
    >>> parse_curie("omim.ps:PS12345")
    ReferenceTuple('omim.ps', '12345')

    Use preferred (available)
    >>> parse_curie("GO_1234", sep="_", use_preferred=True)
    ReferenceTuple('GO', '1234')

    Use preferred (unavailable)
    >>> parse_curie("pdb:1234", use_preferred=True)
    ReferenceTuple('pdb', '1234')
    """
    if strict:
        return manager.parse_curie(
            curie,
            sep=sep,
            use_preferred=use_preferred,
            strict=strict,
        )
    elif on_failure_return_type == FailureReturnType.single:
        return manager.parse_curie(
            curie,
            sep=sep,
            use_preferred=use_preferred,
            on_failure_return_type=on_failure_return_type,
            strict=strict,
        )
    elif on_failure_return_type == FailureReturnType.pair:
        return manager.parse_curie(
            curie,
            sep=sep,
            use_preferred=use_preferred,
            on_failure_return_type=on_failure_return_type,
            strict=strict,
        )
    else:
        raise TypeError
