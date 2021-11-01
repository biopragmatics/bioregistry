# -*- coding: utf-8 -*-

"""Resolvers for CURIE (e.g., pairs of prefix and identifier)."""

import warnings
from typing import Callable, Mapping, Optional, Sequence, Tuple

from .constants import BIOREGISTRY_REMOTE_URL
from .resolve import (
    get_banana,
    get_bioportal_prefix,
    get_identifiers_org_prefix,
    get_namespace_in_lui,
    get_obofoundry_uri_prefix,
    get_ols_prefix,
    get_resource,
    normalize_parsed_curie,
    parse_curie,
)

__all__ = [
    "is_known_identifier",
    "get_providers",
    "get_providers_list",
    "get_identifiers_org_iri",
    "get_identifiers_org_curie",
    "get_obofoundry_uri_prefix",
    "get_obofoundry_iri",
    "get_ols_iri",
    "get_bioportal_iri",
    "get_n2t_iri",
    "get_iri",
    "get_link",
    "miriam_standardize_identifier",
]


def is_known_identifier(prefix: str, identifier: str) -> Optional[bool]:
    """Check that an identifier can be normalized and also matches a prefix's local unique identifier pattern.

    :param prefix: The prefix in the CURIE
    :param identifier: The identifier in the CURIE
    :return: Whether this identifier passes validation, after normalization

    >>> is_known_identifier("chebi", "1234")
    True
    >>> is_known_identifier("chebi", "CHEBI:12345")
    True
    >>> is_known_identifier("chebi", "CHEBI:ABCD")
    False
    """
    resource = get_resource(prefix)
    if resource is None:
        return None
    return resource.is_known_identifier(identifier)


def miriam_standardize_identifier(prefix: str, identifier: str) -> str:
    """Normalize the identifier with the appropriate banana.

    :param prefix: The prefix in the CURIE
    :param identifier: The identifier in the CURIE
    :return: A normalize identifier, possibly with banana/redundant prefix added

    Examples with explicitly annotated bananas:

    >>> assert "VariO" == get_banana('vario')
    >>> miriam_standardize_identifier('vario', '0376')
    'VariO:0376'
    >>> miriam_standardize_identifier('vario', 'VariO:0376')
    'VariO:0376'

    Examples with bananas from OBO:
    >>> assert "FBbt" == get_banana('fbbt')
    >>> miriam_standardize_identifier('fbbt', '00007294')
    'FBbt:00007294'
    >>> miriam_standardize_identifier('fbbt', 'FBbt:00007294')
    'FBbt:00007294'

    Examples from OBO Foundry:
    >>> miriam_standardize_identifier('chebi', '1234')
    'CHEBI:1234'
    >>> miriam_standardize_identifier('chebi', 'CHEBI:1234')
    'CHEBI:1234'

     Examples outside of OBO:
    >>> miriam_standardize_identifier('mgi', '6017782')
    'MGI:6017782'
    >>> miriam_standardize_identifier('mgi', 'MGI:6017782')
    'MGI:6017782'

    >>> miriam_standardize_identifier('swisslipid', '000000341')
    'SLM:000000341'
    >>> miriam_standardize_identifier('swisslipid', 'SLM:000000341')
    'SLM:000000341'

    Standard:

    >>> assert get_banana('pdb') is None
    >>> assert not get_namespace_in_lui('pdb')
    >>> miriam_standardize_identifier('pdb', '00000020')
    '00000020'
    """
    resource = get_resource(prefix)
    if resource is None:
        return identifier  # nothing we can do
    return resource.miriam_standardize_identifier(identifier)


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
    return entry.get_default_uri(identifier)


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
    >>> get_identifiers_org_iri("interpro", "IPR016380")
    'https://identifiers.org/interpro:IPR016380'
    """
    curie = get_identifiers_org_curie(prefix, identifier)
    if curie is None:
        return None
    return f"{IDENTIFIERS_ORG_URL_PREFIX}{curie}"


def get_n2t_iri(prefix: str, identifier: str) -> Optional[str]:
    """Get the name-to-thing URL for the given CURIE.

    :param prefix: The prefix in the CURIE
    :param identifier: The identifier in the CURIE
    :return: A IRI string corresponding to the N2T resolve, if the prefix exists and is
        mapped to N2T.

    >>> get_n2t_iri('chebi', '24867')
    'https://n2t.net/chebi:24867'
    """
    return get_formatted_iri("n2t", prefix, identifier)


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
    elif get_namespace_in_lui(prefix):
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
    return get_formatted_iri("obofoundry", prefix, identifier)


def get_ols_iri(prefix: str, identifier: str) -> Optional[str]:
    """Get the OLS URL if possible."""
    ols_prefix = get_ols_prefix(prefix)
    obo_iri = get_obofoundry_iri(prefix, identifier)
    if ols_prefix is None or obo_iri is None:
        return None
    return f"https://www.ebi.ac.uk/ols/ontologies/{ols_prefix}/terms?iri={obo_iri}"


def get_scholia_iri(prefix: str, identifier: str) -> Optional[str]:
    """Get a Scholia IRI, if possible.

    :param prefix: The prefix in the CURIE
    :param identifier: The identifier in the CURIE
    :return: A link to the Scholia page

    >>> get_scholia_iri("pubmed", "1234")
    'https://scholia.toolforge.org/pubmed/1234'

    >>> get_scholia_iri("pdb", "1234")
    None
    """
    return get_formatted_iri("scholia", prefix, identifier)


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

    >>> get_bioregistry_iri('fbbt', 'fbbt:00007294')
    'https://bioregistry.io/fbbt:00007294'
    >>> get_bioregistry_iri('fbbt', 'fbbt:00007294')
    'https://bioregistry.io/fbbt:00007294'
    >>> get_bioregistry_iri('fbbt', '00007294')
    'https://bioregistry.io/fbbt:00007294'

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
    "scholia": get_scholia_iri,
}

LINK_PRIORITY = [
    "custom",
    "default",
    "bioregistry",
    "miriam",
    "ols",
    "obofoundry",
    "n2t",
    "bioportal",
    "scholia",
]


def get_iri(
    prefix: str,
    identifier: Optional[str] = None,
    *,
    priority: Optional[Sequence[str]] = None,
    prefix_map: Optional[Mapping[str, str]] = None,
    use_bioregistry_io: bool = True,
) -> Optional[str]:
    """Get the best link for the CURIE, if possible.

    :param prefix: The prefix in the CURIE
    :param identifier: The identifier in the CURIE. If identifier is given as None, then this function will
        assume that the first argument (``prefix``) is actually a full CURIE.
    :param priority: A user-defined priority list. In addition to the metaprefixes in the Bioregistry
        corresponding to resources that are resolvers/lookup services, you can also use ``default``
        to correspond to the first-party IRI and ``custom`` to refer to the custom prefix map.
        The default priority list is:

        1. Custom prefix map (``custom``)
        1. First-party IRI (``default``)
        2. Identifiers.org / MIRIAM (``miriam``)
        3. Ontology Lookup Service (``ols``)
        4. OBO PURL (``obofoundry``)
        5. Name-to-Thing (``n2t``)
        6. BioPortal (``bioportal``)
    :param prefix_map: A custom prefix map to go with the ``custom`` key in the priority list
    :param use_bioregistry_io: Should the bioregistry resolution IRI be used? Defaults to true.
    :return: The best possible IRI that can be generated based on the priority list.

    A pre-parse CURIE can be given as the first two arguments
    >>> get_iri("chebi", "24867")
    'https://www.ebi.ac.uk/chebi/searchId.do?chebiId=CHEBI:24867'

    A CURIE can be given directly as a single argument
    >>> get_iri("chebi:24867")
    'https://www.ebi.ac.uk/chebi/searchId.do?chebiId=CHEBI:24867'

    A priority list can be given
    >>> priority = ["obofoundry", "default", "bioregistry"]
    >>> get_iri("chebi:24867", priority=priority)
    'http://purl.obolibrary.org/obo/CHEBI_24867'

    A custom prefix map can be supplied.
    >>> prefix_map = {"chebi": "https://example.org/chebi/"}
    >>> get_iri("chebi:24867", prefix_map=prefix_map)
    'https://example.org/chebi/24867'
    >>> get_iri("fbbt:00007294")
    'https://flybase.org/cgi-bin/cvreport.pl?id=FBbt:00007294'

    A custom prefix map can be supplied in combination with a priority list
    >>> prefix_map = {"lipidmaps": "https://example.org/lipidmaps/"}
    >>> priority = ["obofoundry", "custom", "default", "bioregistry"]
    >>> get_iri("chebi:24867", prefix_map=prefix_map, priority=priority)
    'http://purl.obolibrary.org/obo/CHEBI_24867'
    >>> get_iri("lipidmaps:1234", prefix_map=prefix_map, priority=priority)
    'https://example.org/lipidmaps/1234'
    """
    if identifier is None:
        _prefix, _identifier = parse_curie(prefix)
        if _prefix is None or _identifier is None:
            return None
    else:
        _prefix, _identifier = prefix, identifier

    providers = dict(get_providers(_prefix, _identifier))
    if prefix_map and _prefix in prefix_map:
        providers["custom"] = f"{prefix_map[_prefix]}{_identifier}"
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


def get_formatted_iri(metaprefix: str, prefix: str, identifier: str) -> Optional[str]:
    """Get an IRI using the format in the metaregistry.

    :param metaprefix: The metaprefix of the registry in the metaregistry
    :param prefix: A bioregistry prefix (will be mapped to the external one automatically)
    :param identifier: The identifier for the entity
    :returns: An IRI generated from the ``resolver_url`` format string of the registry, if it
        exists.

    >>> get_formatted_iri("miriam", "hgnc", "16793")
    'https://identifiers.org/hgnc:16793'
    >>> get_formatted_iri("n2t", "hgnc", "16793")
    'https://n2t.net/hgnc:16793'
    >>> get_formatted_iri("obofoundry", "fbbt", "00007294")
    'http://purl.obolibrary.org/obo/FBbt_00007294'
    >>> get_formatted_iri("scholia", "lipidmaps", "00000052")
    'https://scholia.toolforge.org/lipidmaps/00000052'
    """
    from .metaresource_api import get_registry

    resource = get_resource(prefix)
    if resource is None:
        return None
    mapped_prefix = resource.get_mapped_prefix(metaprefix)
    if mapped_prefix is None:
        return None
    registry = get_registry(metaprefix)
    if registry is None:
        return None
    return registry.resolve(mapped_prefix, identifier)
