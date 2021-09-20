# -*- coding: utf-8 -*-

"""Resolvers for CURIE (e.g., pairs of prefix and identifier)."""

import warnings
from typing import Callable, Mapping, Optional, Sequence, Tuple

from .constants import BIOREGISTRY_REMOTE_URL
from .resolve import (
    get_banana,
    get_bioportal_prefix,
    get_identifiers_org_prefix,
    get_n2t_prefix,
    get_obofoundry_format,
    get_ols_prefix,
    get_pattern_re,
    get_resource,
    namespace_in_lui,
    normalize_parsed_curie,
    parse_curie,
)

__all__ = [
    "validate",
    "get_providers",
    "get_providers_list",
    "get_identifiers_org_iri",
    "get_identifiers_org_curie",
    "get_obofoundry_format",
    "get_obofoundry_iri",
    "get_ols_iri",
    "get_bioportal_iri",
    "get_n2t_iri",
    "get_iri",
    "get_link",
    "normalize_identifier",
]


def validate(prefix: str, identifier: str) -> Optional[bool]:
    """Validate the identifier against the prefix's pattern, if it exists."""
    pattern = get_pattern_re(prefix)
    if pattern is None:
        return None
    return bool(pattern.match(normalize_identifier(prefix, identifier)))


def normalize_identifier(prefix: str, identifier: str) -> str:
    """Normalize the identifier with the appropriate banana.

    :param prefix: The prefix in the CURIE
    :param identifier: The identifier in the CURIE
    :return: A normalize identifier, possibly with banana/redundant prefix added

    Examples with explicitly annotated bananas:

    >>> assert "VariO" == get_banana('vario')
    >>> normalize_identifier('vario', '0376')
    'VariO:0376'
    >>> normalize_identifier('vario', 'VariO:0376')
    'VariO:0376'

    Examples with bananas from OBO:
    >>> assert "FBbt" == get_banana('fbbt')
    >>> normalize_identifier('fbbt', '00007294')
    'FBbt:00007294'
    >>> normalize_identifier('fbbt', 'FBbt:00007294')
    'FBbt:00007294'

    Examples from OBO Foundry:

    >>> assert get_banana('chebi') is None
    >>> normalize_identifier('chebi', '1234')
    'CHEBI:1234'
    >>> normalize_identifier('chebi', 'CHEBI:1234')
    'CHEBI:1234'

    Standard:

    >>> assert get_banana('pdb') is None
    >>> assert not namespace_in_lui('pdb')
    >>> normalize_identifier('pdb', '00000020')
    '00000020'
    """
    resource = get_resource(prefix)
    if resource is None:
        return identifier  # nothing we can do

    # A "banana" is an embedded prefix that isn't actually part of the identifier.
    # Usually this corresponds to the prefix itself, with some specific stylization
    # such as in the case of FBbt. The banana does NOT include a colon ":" at the end
    banana = resource.get_banana()
    if banana:
        banana = f"{banana}:"
        if not identifier.startswith(banana):
            return f"{banana}{identifier}"
    # Handle when the namespace is in the LUI, but no specific banana
    # has been given. This is most common for OBO Foundry ontologies'
    # identifiers, like CHEBI:XXXX
    elif resource.namespace_in_lui():
        banana = f"{prefix.upper()}:"
        if not identifier.startswith(banana):
            return f"{banana}{identifier}"

    # TODO Unnecessary redundant prefix?
    # elif identifier.lower().startswith(f'{prefix}:'):
    #

    return identifier


def get_default_iri(prefix: str, identifier: str) -> Optional[str]:
    """Get the default URL for the given CURIE.

    :param prefix: The prefix in the CURIE
    :param identifier: The identifier in the CURIE
    :return: A IRI string corresponding to the default provider, if available.

    >>> get_default_iri('chebi', '24867')
    'https://www.ebi.ac.uk/chebi/searchId.do?chebiId=CHEBI:24867'
    """
    entry = get_resource(prefix)
    if entry is None:
        return None
    return entry.get_default_url(identifier)


def get_providers(prefix: str, identifier: str) -> Mapping[str, str]:
    """Get all providers for the CURIE."""
    return dict(get_providers_list(prefix, identifier))


def get_providers_list(prefix: str, identifier: str) -> Sequence[Tuple[str, str]]:
    """Get all providers for the CURIE."""
    rv = []
    for provider, get_url in PROVIDER_FUNCTIONS.items():
        link = get_url(prefix, identifier)
        if link is not None:
            rv.append((provider, link))
    if not rv:
        return rv

    bioregistry_link = get_bioregistry_iri(prefix, identifier)
    if not bioregistry_link:
        return rv

    # if a default URL is available, it goes first. otherwise the bioregistry URL goes first.
    rv.insert(1 if rv[0][0] == "default" else 0, ("bioregistry", bioregistry_link))
    return rv


IDENTIFIERS_ORG_URL_PREFIX = "https://identifiers.org/"


def get_identifiers_org_iri(prefix: str, identifier: str) -> Optional[str]:
    """Get the identifiers.org URL for the given CURIE.

    :param prefix: The prefix in the CURIE
    :param identifier: The identifier in the CURIE
    :return: A IRI string corresponding to the Identifiers.org, if the prefix exists and is
        mapped to MIRIAM.

    >>> get_identifiers_org_iri('chebi', '24867')
    'https://identifiers.org/CHEBI:24867'
    """
    curie = get_identifiers_org_curie(prefix, identifier)
    if curie is None:
        return None
    return f"{IDENTIFIERS_ORG_URL_PREFIX}{curie}"


N2T_URL_PREFIX = "https://n2t.net/"


def get_n2t_iri(prefix: str, identifier: str) -> Optional[str]:
    """Get the name-to-thing URL for the given CURIE.

    :param prefix: The prefix in the CURIE
    :param identifier: The identifier in the CURIE
    :return: A IRI string corresponding to the N2T resolve, if the prefix exists and is
        mapped to N2T.

    >>> get_n2t_iri('chebi', '24867')
    'https://n2t.net/chebi:24867'
    """
    n2t_prefix = get_n2t_prefix(prefix)
    if n2t_prefix is None:
        return None
    return f"{N2T_URL_PREFIX}{n2t_prefix}:{identifier}"


def get_bioportal_iri(prefix: str, identifier: str) -> Optional[str]:
    """Get the Bioportal URL for the given CURIE.

    :param prefix: The prefix in the CURIE
    :param identifier: The identifier in the CURIE
    :return: A link to the Bioportal page

    >>> get_bioportal_iri('chebi', '24431')
    'https://bioportal.bioontology.org/ontologies/CHEBI/?p=classes&conceptid=http://purl.obolibrary.org/obo/CHEBI_24431'
    """
    bioportal_prefix = get_bioportal_prefix(prefix)
    if bioportal_prefix is None:
        return None
    obo_link = get_obofoundry_iri(prefix, identifier)
    if obo_link is not None:
        return f"https://bioportal.bioontology.org/ontologies/{bioportal_prefix}/?p=classes&conceptid={obo_link}"
    # TODO there must be other rules?
    return None


# MIRIAM definitions that don't make any sense
MIRIAM_BLACKLIST = {
    # this one uses the names instead of IDs, and points to a dead resource.
    # See https://github.com/identifiers-org/identifiers-org.github.io/issues/139
    "pid.pathway",
}


def get_identifiers_org_curie(prefix: str, identifier: str) -> Optional[str]:
    """Get the identifiers.org CURIE for the given CURIE."""
    miriam_prefix = get_identifiers_org_prefix(prefix)
    if miriam_prefix is None or miriam_prefix in MIRIAM_BLACKLIST:
        return None
    banana = get_banana(prefix)
    if banana:
        if identifier.startswith(f"{banana}:"):
            return identifier
        else:
            return f"{banana}:{identifier}"
    elif namespace_in_lui(prefix):
        if identifier.startswith(prefix.upper()):
            return identifier
        else:
            return f"{prefix.upper()}:{identifier}"
    else:
        return f"{miriam_prefix}:{identifier}"


def get_obofoundry_iri(prefix: str, identifier: str) -> Optional[str]:
    """Get the OBO Foundry URL if possible.

    :param prefix: The prefix
    :param identifier: The identifier
    :return: The OBO Foundry URL if the prefix can be mapped to an OBO Foundry entry

    >>> get_obofoundry_iri('chebi', '24431')
    'http://purl.obolibrary.org/obo/CHEBI_24431'

    For entries where there's a preferred prefix, it is respected.

    >>> get_obofoundry_iri('fbbt', '00007294')
    'http://purl.obolibrary.org/obo/FBbt_00007294'
    """
    fmt = get_obofoundry_format(prefix)
    if fmt is None:
        return None
    return f"{fmt}{identifier}"


def get_ols_iri(prefix: str, identifier: str) -> Optional[str]:
    """Get the OLS URL if possible."""
    ols_prefix = get_ols_prefix(prefix)
    obo_iri = get_obofoundry_iri(prefix, identifier)
    if ols_prefix is None or obo_iri is None:
        return None
    return f"https://www.ebi.ac.uk/ols/ontologies/{ols_prefix}/terms?iri={obo_iri}"


def get_bioregistry_iri(prefix: str, identifier: str) -> Optional[str]:
    """Get the bioregistry link.

    :param prefix: The prefix in the CURIE
    :param identifier: The identifier in the CURIE
    :return: A link to the bioregistry resolver

    >>> get_bioregistry_iri('pdb', '1234')
    'https://bioregistry.io/pdb:1234'

    Redundant prefix (OBO)

    >>> get_bioregistry_iri('go', 'GO:0120212')
    'https://bioregistry.io/go:0120212'
    >>> get_bioregistry_iri('go', 'go:0120212')
    'https://bioregistry.io/go:0120212'
    >>> get_bioregistry_iri('go', '0120212')
    'https://bioregistry.io/go:0120212'

    Redundant prefix (banana; OBO)

    >>> get_bioregistry_iri('fbbt', 'FBbt:1234')
    'https://bioregistry.io/fbbt:1234'
    >>> get_bioregistry_iri('fbbt', 'fbbt:1234')
    'https://bioregistry.io/fbbt:1234'
    >>> get_bioregistry_iri('fbbt', '1234')
    'https://bioregistry.io/fbbt:1234'

    Redundant prefix (banana; explicit)
    >>> get_bioregistry_iri('go.ref', 'GO_REF:1234')
    'https://bioregistry.io/go.ref:1234'
    >>> get_bioregistry_iri('go.ref', '1234')
    'https://bioregistry.io/go.ref:1234'
    """
    norm_prefix, norm_identifier = normalize_parsed_curie(prefix, identifier)
    if norm_prefix is None:
        return None
    return f"{BIOREGISTRY_REMOTE_URL.rstrip()}/{norm_prefix}:{norm_identifier}"


PROVIDER_FUNCTIONS: Mapping[str, Callable[[str, str], Optional[str]]] = {
    "default": get_default_iri,
    "miriam": get_identifiers_org_iri,
    "obofoundry": get_obofoundry_iri,
    "ols": get_ols_iri,
    "n2t": get_n2t_iri,
    "bioportal": get_bioportal_iri,
}

LINK_PRIORITY = [
    "default",
    "bioregistry",
    "miriam",
    "ols",
    "obofoundry",
    "n2t",
    "bioportal",
]


def get_iri(
    prefix: str,
    identifier: Optional[str] = None,
    priority: Optional[Sequence[str]] = None,
    use_bioregistry_io: bool = True,
) -> Optional[str]:
    """Get the best link for the CURIE, if possible.

    :param prefix: The prefix in the CURIE
    :param identifier: The identifier in the CURIE. If identifier is given as None, then this function will
        assume that the first argument (``prefix``) is actually a full CURIE.
    :param priority: A user-defined priority list. In addition to the metaprefixes in the Bioregistry
        corresponding to resources that are resolvers/lookup services, you can also use ``default``
        to correspond to the first-party IRI. The default priority list is:

        1. First-party IRI (``default``)
        2. Identifiers.org / MIRIAM
        3. Ontology Lookup Service
        4. OBO PURL
        5. Name-to-Thing
        6. BioPortal
    :param use_bioregistry_io: Should the bioregistry resolution IRI be used? Defaults to true.
    :return: The best possible IRI that can be generated based on the priority list.

    A pre-parse CURIE can be given as the first two arguments
    >>> get_iri("chebi", "24867")
    'https://www.ebi.ac.uk/chebi/searchId.do?chebiId=CHEBI:24867'

    A CURIE can be given directly as a single argument
    >>> get_iri("chebi:24867")
    'https://www.ebi.ac.uk/chebi/searchId.do?chebiId=CHEBI:24867'
    """
    if identifier is None:
        _prefix, _identifier = parse_curie(prefix)
        if _prefix is None or _identifier is None:
            return None
    else:
        _prefix, _identifier = prefix, identifier

    providers = get_providers(_prefix, _identifier)
    for key in priority or LINK_PRIORITY:
        if not use_bioregistry_io and key == "bioregistry":
            continue
        if key not in providers:
            continue
        rv = providers[key]
        if rv is not None:
            return rv
    return None


def get_link(
    prefix: str,
    identifier: str,
    priority: Optional[Sequence[str]] = None,
    use_bioregistry_io: bool = True,
) -> Optional[str]:
    """Get the best link for the CURIE, if possible."""
    warnings.warn("get_link() is deprecated. use bioregistry.get_iri() instead", DeprecationWarning)
    return get_iri(prefix=prefix, identifier=identifier, use_bioregistry_io=use_bioregistry_io)
