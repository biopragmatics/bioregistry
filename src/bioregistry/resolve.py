# -*- coding: utf-8 -*-

"""Utilities for normalizing prefixes."""

import logging
import re
import warnings
from functools import lru_cache
from typing import Any, Callable, Dict, Mapping, Optional, Sequence, Set, Tuple, Union

from .constants import LICENSES
from .schema import Collection, Registry, Resource
from .utils import read_collections, read_metaregistry, read_registry

__all__ = [
    "get_resource",
    "get_name",
    "get_description",
    "get_mappings",
    "get_synonyms",
    "get_pattern",
    "get_pattern_re",
    "namespace_in_lui",
    "get_format",
    "get_format_url",
    "get_example",
    "has_no_terms",
    "is_deprecated",
    "get_email",
    "get_homepage",
    "get_obo_download",
    "get_json_download",
    "get_owl_download",
    "get_version",
    "get_versions",
    # CURIE handling
    "normalize_prefix",
    "parse_curie",
    "normalize_curie",
    # Metaregistry stuff
    "get_registry",
    "get_registry_name",
    "get_registry_url",
    "get_registry_homepage",
    # Collection stuff
    "get_collection",
]

logger = logging.getLogger(__name__)

# not a perfect email regex, but close enough
EMAIL_RE = re.compile(r"^(\w|\.|\_|\-)+[@](\w|\_|\-|\.)+[.]\w{2,5}$")


def get_resource(prefix: str) -> Optional[Resource]:
    """Get the Bioregistry entry for the given prefix.

    :param prefix: The prefix to look up, which is normalized with :func:`normalize_prefix`
        before lookup in the Bioregistry
    :returns: The Bioregistry entry dictionary, which includes several keys cross-referencing
        other registries when available.
    """
    norm_prefix = normalize_prefix(prefix)
    if norm_prefix is None:
        return None
    return read_registry().get(norm_prefix)


def get(prefix: str) -> Optional[Resource]:
    """Get the Bioregistry entry for the given prefix, deprecated for :func:`get_resource`."""
    warnings.warn("use bioregistry.get_resource", DeprecationWarning)
    return get_resource(prefix)


def get_collection(identifier: str) -> Optional[Collection]:
    """Get the metaregistry entry for the given identifier."""
    return read_collections().get(identifier)


def get_registry(metaprefix: str) -> Optional[Registry]:
    """Get the metaregistry entry for the given prefix."""
    return read_metaregistry().get(metaprefix)


def get_registry_name(metaprefix: str) -> Optional[str]:
    """Get the metaregistry name for the given prefix, if it's available."""
    registry = get_registry(metaprefix)
    if registry is None:
        return None
    return registry.name


def get_registry_homepage(metaprefix: str) -> Optional[str]:
    """Get the URL for the registry, if available.

    :param metaprefix: The metaprefix of the registry
    :return: The URL for the registry, if available, otherwise ``None``.

    >>> get_registry_homepage('biolink')
    'https://raw.githubusercontent.com/biolink/biolink-model'

    ``None`` is returned on missing values.

    >>> get_registry_homepage('missing')
    None
    """
    registry = get_registry(metaprefix)
    if registry is None:
        return None
    return registry.homepage


def get_registry_description(metaprefix: str) -> Optional[str]:
    """Get the description for the registry, if available.

    :param metaprefix: The metaprefix of the registry
    :return: The description for the registry, if available, otherwise ``None``.

    >>> get_registry_description('prefixcommons')
    'A registry of commonly used prefixes in the life sciences and linked data'

    >>> get_registry_description('missing')
    None
    """
    registry = get_registry(metaprefix)
    if registry is None:
        return None
    return registry.description


def get_registry_example(metaprefix: str) -> Optional[str]:
    """Get an example for the registry, if available."""
    registry = get_registry(metaprefix)
    if registry is None:
        return None
    return registry.example


def get_registry_url(metaprefix: str, prefix: str) -> Optional[str]:
    """Get the URL for the resource inside registry, if available."""
    entry = get_registry(metaprefix)
    if entry is None:
        return None
    return entry.get_provider(prefix)


def get_name(prefix: str) -> Optional[str]:
    """Get the name for the given prefix, it it's available."""
    return _get_prefix_key(
        prefix, "name", ("obofoundry", "ols", "wikidata", "go", "ncbi", "bioportal", "miriam")
    )


def get_description(prefix: str) -> Optional[str]:
    """Get the description for the given prefix, if available."""
    return _get_prefix_key(prefix, "description", ("miriam", "ols", "obofoundry", "wikidata"))


def get_mappings(prefix: str) -> Optional[Mapping[str, str]]:
    """Get the mappings to external registries, if available."""
    entry = get_resource(prefix)
    if entry is None:
        return None
    rv: Dict[str, str] = {}
    rv.update(entry.mappings or {})  # This will be the replacement later
    for metaprefix in read_metaregistry():
        external = get_external(prefix, metaprefix)
        if not external:
            continue
        if metaprefix == "wikidata":
            value = external.get("prefix")
            if value is not None:
                rv["wikidata"] = value
        elif metaprefix == "obofoundry":
            rv[metaprefix] = external.get("preferredPrefix", external["prefix"].upper())
        else:
            rv[metaprefix] = external["prefix"]

    return rv


def get_synonyms(prefix: str) -> Optional[Set[str]]:
    """Get the synonyms for a given prefix, if available."""
    entry = get_resource(prefix)
    if entry is None:
        return None
    # TODO aggregate even more from xrefs
    return set(entry.synonyms or {})


def _get_prefix_key(prefix: str, key: str, metaprefixes: Sequence[str]):
    # This function doesn't have a type annotation since there are different
    # kinds of values that might come out (str or bool)
    entry = get_resource(prefix)
    if entry is None:
        return None
    return entry.get_prefix_key(key, metaprefixes)


def get_pattern(prefix: str) -> Optional[str]:
    """Get the pattern for the given prefix, if it's available.

    :param prefix: The prefix to look up, which is normalized with :func:`normalize_prefix`
        before lookup in the Bioregistry
    :returns: The pattern for the prefix, if it is available, using the following order of preference:
        1. Custom
        2. MIRIAM
        3. Wikidata
    """
    return _get_prefix_key(prefix, "pattern", ("miriam", "wikidata"))


@lru_cache()
def get_pattern_re(prefix: str):
    """Get the compiled pattern for the given prefix, if it's available."""
    pattern = get_pattern(prefix)
    if pattern is None:
        return None
    return re.compile(pattern)


def namespace_in_lui(prefix: str) -> Optional[bool]:
    """Check if the namespace should appear in the LUI."""
    return _get_prefix_key(prefix, "namespaceEmbeddedInLui", ("miriam",))


def get_identifiers_org_prefix(prefix: str) -> Optional[str]:
    """Get the identifiers.org prefix if available.

    :param prefix: The prefix to lookup.
    :returns: The Identifiers.org/MIRIAM prefix corresponding to the prefix, if mappable.

    >>> import bioregistry
    >>> bioregistry.get_identifiers_org_prefix('chebi')
    'chebi'
    >>> bioregistry.get_identifiers_org_prefix('ncbitaxon')
    'taxonomy'
    >>> assert bioregistry.get_identifiers_org_prefix('MONDO') is None
    """
    return _get_mapped_prefix(prefix, "miriam")


def get_n2t_prefix(prefix: str) -> Optional[str]:
    """Get the name-to-thing prefix if available."""
    return _get_mapped_prefix(prefix, "n2t")


def get_wikidata_prefix(prefix: str) -> Optional[str]:
    """Get the wikidata prefix if available."""
    return _get_mapped_prefix(prefix, "wikidata")


def get_bioportal_prefix(prefix: str) -> Optional[str]:
    """Get the Bioportal prefix if available."""
    return _get_mapped_prefix(prefix, "bioportal")


def get_obofoundry_prefix(prefix: str) -> Optional[str]:
    """Get the OBO Foundry prefix if available."""
    return _get_mapped_prefix(prefix, "obofoundry")


def get_registry_map(metaprefix: str) -> Dict[str, str]:
    """Get a mapping from the Bioregistry prefixes to prefixes in another registry."""
    rv = {}
    for prefix in read_registry():
        mapped_prefix = _get_mapped_prefix(prefix, metaprefix)
        if mapped_prefix is not None:
            rv[prefix] = mapped_prefix
    return rv


def get_obofoundry_format(prefix: str) -> Optional[str]:
    """Get the URL format for an OBO Foundry entry.

    :param prefix: The prefix to lookup.
    :returns: The OBO PURL URL prefix corresponding to the prefix, if mappable.

    >>> import bioregistry
    >>> bioregistry.get_obofoundry_format('go')  # standard
    'http://purl.obolibrary.org/obo/GO_'
    >>> bioregistry.get_obofoundry_format('ncbitaxon')  # mixed case
    'http://purl.obolibrary.org/obo/NCBITaxon_'
    >>> assert bioregistry.get_obofoundry_format('sty') is None
    """
    obo_prefix = get_obofoundry_prefix(prefix)
    if obo_prefix is None:
        return None
    return f"http://purl.obolibrary.org/obo/{obo_prefix}_"


def get_ols_prefix(prefix: str) -> Optional[str]:
    """Get the OLS prefix if available."""
    return _get_mapped_prefix(prefix, "ols")


def get_fairsharing_prefix(prefix: str) -> Optional[str]:
    """Get the FAIRSharing prefix if available."""
    return _get_mapped_prefix(prefix, "fairsharing")


def _get_mapped_prefix(prefix: str, external: str) -> Optional[str]:
    entry = get_mappings(prefix)
    if entry is None:
        return None
    return entry.get(external)


def get_banana(prefix: str) -> Optional[str]:
    """Get the optional redundant prefix to go before an identifier.

    A "banana" is an embedded prefix that isn't actually part of the identifier.
    Usually this corresponds to the prefix itself, with some specific stylization
    such as in the case of FBbt. The banana does NOT include a colon ":" at the end

    :param prefix: The name of the prefix (possibly unnormalized)
    :return: The banana, if the prefix is valid and has an associated banana.

    Explicitly annotated banana
    >>> assert "GO_REF" == get_banana('go.ref')

    Banana imported through OBO Foundry
    >>> assert "FBbt" == get_banana('fbbt')

    No banana (ChEBI does have namespace in LUI, though)
    >>> assert get_banana('chebi') is None

    No banana, no namespace in LUI
    >>> assert get_banana('pdb') is None
    """
    entry = get_resource(prefix)
    if entry is None:
        return None
    if entry.banana is not None:
        return entry.banana
    if entry.obofoundry and "preferredPrefix" in entry.obofoundry:
        return entry.obofoundry["preferredPrefix"]
    return None


DEFAULT_FORMAT_PRIORITY = (
    "bioregistry",
    "obofoundry",
    "prefixcommons",
    "miriam",
    "ols",
)


def get_format(prefix: str, priority: Optional[Sequence[str]] = None) -> Optional[str]:
    """Get the URL format string for the given prefix, if it's available.

    :param prefix: The name of the prefix (possibly unnormalized)
    :param priority: The priority order of metaresources to use for format URL lookup.
        The default is:

        1. Bioregistry
        2. OBO Foundry
        3. Prefix Commons
        4. Identifiers.org / MIRIAM
        5. OLS
    :return: The best URL format string, where the ``$1`` should be replaced by the
        identifier. ``$1`` could potentially appear multiple times.

    >>> import bioregistry
    >>> bioregistry.get_format('chebi')
    'https://www.ebi.ac.uk/chebi/searchId.do?chebiId=CHEBI:$1'

    If you want to specify a different priority order, you can do so with the ``priority`` keyword. This
    is of particular interest to ontologists and semantic web people who might want to use ``purl.obolibrary.org``
    URL prefixes over the URL prefixes corresponding to the first-party providers for each resource (e.g., the
    ChEBI example above). Do so like:

    >>> import bioregistry
    >>> bioregistry.get_format('chebi', priority=['obofoundry', 'bioregistry', 'prefixcommons', 'miriam', 'ols'])
    'http://purl.obolibrary.org/obo/CHEBI_$1'
    """
    entry = get_resource(prefix)
    if entry is None:
        return None
    for metaprefix in priority or DEFAULT_FORMAT_PRIORITY:
        formatter = FORMATTERS[metaprefix]
        rv = formatter(prefix)
        if rv is not None:
            return rv
    return None


def _get_bioregistry_format(prefix: str) -> Optional[str]:
    entry = get_resource(prefix)
    if entry is None:
        return None
    if entry.url:
        return entry.url
    rv = get_external(prefix, "miriam").get("provider_url")
    if rv is not None:
        return rv
    rv = get_external(prefix, "prefixcommons").get("formatter")
    if rv is not None:
        return rv
    rv = get_external(prefix, "wikidata").get("format")
    if rv is not None:
        return rv
    return None


def get_miriam_url_prefix(prefix: str) -> Optional[str]:
    """Get the URL format for a MIRIAM entry.

    :param prefix: The prefix to lookup.
    :returns: The Identifiers.org/MIRIAM URL format string, if available.

    >>> import bioregistry
    >>> bioregistry.get_miriam_url_prefix('ncbitaxon')
    'https://identifiers.org/taxonomy:'
    >>> bioregistry.get_miriam_url_prefix('go')
    'https://identifiers.org/GO:'
    >>> assert bioregistry.get_miriam_url_prefix('sty') is None
    """
    miriam_prefix = get_identifiers_org_prefix(prefix)
    if miriam_prefix is None:
        return None
    if namespace_in_lui(prefix):
        # not exact solution, some less common ones don't use capitalization
        # align with the banana solution
        miriam_prefix = miriam_prefix.upper()
    return f"https://identifiers.org/{miriam_prefix}:"


def get_miriam_format(prefix: str) -> Optional[str]:
    """Get the URL format for a MIRIAM entry.

    :param prefix: The prefix to lookup.
    :returns: The Identifiers.org/MIRIAM URL format string, if available.

    >>> import bioregistry
    >>> bioregistry.get_miriam_format('ncbitaxon')
    'https://identifiers.org/taxonomy:$1'
    >>> bioregistry.get_miriam_format('go')
    'https://identifiers.org/GO:$1'
    >>> assert bioregistry.get_miriam_format('sty') is None
    """
    miriam_url_prefix = get_miriam_url_prefix(prefix)
    if miriam_url_prefix is None:
        return None
    return f"{miriam_url_prefix}$1"


def get_obofoundry_formatter(prefix: str) -> Optional[str]:
    """Get the URL format for an OBO Foundry entry.

    :param prefix: The prefix to lookup.
    :returns: The OBO PURL format string, if available.

    >>> import bioregistry
    >>> bioregistry.get_obofoundry_formatter('go')  # standard
    'http://purl.obolibrary.org/obo/GO_$1'
    >>> bioregistry.get_obofoundry_formatter('ncbitaxon')  # mixed case
    'http://purl.obolibrary.org/obo/NCBITaxon_$1'
    >>> assert bioregistry.get_obofoundry_formatter('sty') is None
    """
    rv = get_obofoundry_format(prefix)
    if rv is None:
        return None
    return f"{rv}$1"


def get_ols_url_prefix(prefix: str) -> Optional[str]:
    """Get the URL format for an OLS entry.

    :param prefix: The prefix to lookup.
    :returns: The OLS format string, if available.

    .. warning:: This doesn't have a normal form, so it only works for OBO Foundry at the moment.

    >>> import bioregistry
    >>> bioregistry.get_ols_url_prefix('go')  # standard
    'https://www.ebi.ac.uk/ols/ontologies/go/terms?iri=http://purl.obolibrary.org/obo/GO_'
    >>> bioregistry.get_ols_url_prefix('ncbitaxon')  # mixed case
    'https://www.ebi.ac.uk/ols/ontologies/ncbitaxon/terms?iri=http://purl.obolibrary.org/obo/NCBITaxon_'
    >>> assert bioregistry.get_ols_url_prefix('sty') is None
    """
    ols_prefix = get_ols_prefix(prefix)
    if ols_prefix is None:
        return None
    obo_format = get_obofoundry_format(prefix)
    if obo_format:
        return f"https://www.ebi.ac.uk/ols/ontologies/{ols_prefix}/terms?iri={obo_format}"
    # TODO find examples, like for EFO on when it's not based on OBO Foundry PURLs
    return None


def get_ols_format(prefix: str) -> Optional[str]:
    """Get the URL format for an OLS entry.

    :param prefix: The prefix to lookup.
    :returns: The OLS format string, if available.

    .. warning:: This doesn't have a normal form, so it only works for OBO Foundry at the moment.

    >>> import bioregistry
    >>> bioregistry.get_ols_format('go')  # standard
    'https://www.ebi.ac.uk/ols/ontologies/go/terms?iri=http://purl.obolibrary.org/obo/GO_$1'
    >>> bioregistry.get_ols_format('ncbitaxon')  # mixed case
    'https://www.ebi.ac.uk/ols/ontologies/ncbitaxon/terms?iri=http://purl.obolibrary.org/obo/NCBITaxon_$1'
    >>> assert bioregistry.get_ols_format('sty') is None
    """
    ols_url_prefix = get_ols_url_prefix(prefix)
    if ols_url_prefix is None:
        return None
    return f"{ols_url_prefix}$1"


def get_prefixcommons_format(prefix: str) -> Optional[str]:
    """Get the URL format for a Prefix Commons entry.

    :param prefix: The prefix to lookup.
    :returns: The Prefix Commons URL format string, if available.

    >>> import bioregistry
    >>> bioregistry.get_prefixcommons_format('hgmd')
    'http://www.hgmd.cf.ac.uk/ac/gene.php?gene=$1'
    """
    return get_external(prefix, "prefixcommons").get("formatter")


def get_external(prefix: str, metaprefix: str) -> Mapping[str, Any]:
    """Get the external data for the entry."""
    norm_prefix = normalize_prefix(prefix)
    if norm_prefix is None:
        return {}
    entry = read_registry()[norm_prefix]
    return entry.get_external(metaprefix)


def get_format_urls(
    *,
    priority: Optional[Sequence[str]] = None,
    include_synonyms: bool = False,
) -> Mapping[str, str]:
    """Get a mapping from Bioregistry prefixes to their prefix URLs via :func:`get_format_url`.

    :param priority: A priority list for how to generate prefix URLs.
    :param include_synonyms: Should synonyms of each prefix also be included as additional prefixes, but with
        the same URL prefix?
    :return: A mapping from prefixes to prefix URLs.
    """
    rv = {}
    for prefix in read_registry():
        prefix_url = get_format_url(prefix, priority=priority)
        if prefix_url is None:
            continue
        rv[prefix] = prefix_url
        if include_synonyms:
            for synonym in get_synonyms(prefix) or []:
                rv[synonym] = prefix_url
    return rv


def get_format_url(prefix: str, priority: Optional[Sequence[str]] = None) -> Optional[str]:
    """Get a well-formed format URL for usage in a prefix map.

    :param prefix: The prefix to lookup.
    :param priority: The prioirty order for :func:`get_format`.
    :return: The URL prefix. Similar to what's returned by :func:`bioregistry.get_format`, but
        it MUST have only one ``$1`` and end with ``$1`` to use thie function.

    >>> import bioregistry
    >>> bioregistry.get_format_url('chebi')
    'https://www.ebi.ac.uk/chebi/searchId.do?chebiId=CHEBI:'
    """
    fmt = get_format(prefix, priority=priority)
    if fmt is None:
        logging.warning("term missing formatter: %s", prefix)
        return None
    count = fmt.count("$1")
    if 0 == count:
        logging.warning("formatter missing $1: %s", prefix)
        return None
    if fmt.count("$1") != 1:
        logging.warning("formatter has multiple $1: %s", prefix)
        return None
    if not fmt.endswith("$1"):
        logging.warning("formatter does not end with $1: %s", prefix)
        return None
    return fmt[: -len("$1")]


def get_example(prefix: str) -> Optional[str]:
    """Get an example identifier, if it's available."""
    entry = get_resource(prefix)
    if entry is None:
        return None
    example = entry.example
    if example is not None:
        return example
    miriam_example = get_external(prefix, "miriam").get("sampleId")
    if miriam_example is not None:
        return miriam_example
    example = get_external(prefix, "ncbi").get("example")
    if example is not None:
        return example
    return None


def has_no_terms(prefix: str) -> bool:
    """Check if the prefix is specifically noted to not have terms."""
    entry = get_resource(prefix)
    if entry is None or entry.no_own_terms is None:
        return False
    return entry.no_own_terms


def is_deprecated(prefix: str) -> bool:
    """Return if the given prefix corresponds to a deprecated resource.

    :param prefix: The prefix to lookup
    :returns: If the prefix has been explicitly marked as deprecated either by
        the Bioregistry, OBO Foundry, OLS, or MIRIAM. If no marks are present,
        assumed not to be deprecated.

    >>> import bioregistry
    >>> assert bioregistry.is_deprecated('imr')  # marked by OBO
    >>> assert bioregistry.is_deprecated('iro') # marked by Bioregistry
    >>> assert bioregistry.is_deprecated('miriam.collection') # marked by MIRIAM
    """
    entry = get_resource(prefix)
    if entry is None:
        return False
    if entry.deprecated:
        return True
    for key in ("obofoundry", "ols", "miriam"):
        external = entry.get_external(key)
        if external.get("deprecated"):
            return True
    return False


def get_email(prefix: str) -> Optional[str]:
    """Return the contact email, if available.

    :param prefix: The prefix to lookup
    :returns: The resource's contact email address, if it is available.

    >>> import bioregistry
    >>> bioregistry.get_email('bioregistry')  # from bioregistry curation
    'cthoyt@gmail.com'
    >>> bioregistry.get_email('chebi')
    'amalik@ebi.ac.uk'
    >>> assert bioregistry.get_email('pass2') is None  # dead resource
    """
    rv = _get_prefix_key(prefix, "contact", ("obofoundry", "ols"))
    if rv and not EMAIL_RE.match(rv):
        logger.warning("[%s] invalid email address listed: %s", prefix, rv)
        return None
    return rv


def get_homepage(prefix: str) -> Optional[str]:
    """Return the homepage, if available."""
    return _get_prefix_key(
        prefix, "homepage", ("obofoundry", "ols", "n2t", "wikidata", "go", "ncbi")
    )


def get_obo_download(prefix: str) -> Optional[str]:
    """Get the download link for the latest OBO file."""
    entry = get_resource(prefix)
    if entry is None:
        return None
    if entry.download_obo:
        return entry.download_obo
    return get_external(prefix, "obofoundry").get("download.obo")


def get_json_download(prefix: str) -> Optional[str]:
    """Get the download link for the latest OBOGraph JSON file."""
    entry = get_resource(prefix)
    if entry is None:
        return None
    return get_external(prefix, "obofoundry").get("download.json")


def get_owl_download(prefix: str) -> Optional[str]:
    """Get the download link for the latest OWL file."""
    entry = get_resource(prefix)
    if entry is None:
        return None
    if entry.download_owl:
        return entry.download_owl
    return (
        get_external(prefix, "ols").get("version.iri")
        or get_external(prefix, "ols").get("download")
        or get_external(prefix, "obofoundry").get("download.owl")
    )


def is_provider(prefix: str) -> bool:
    """Get if the prefix is a provider.

    :param prefix: The prefix to look up
    :returns: if the prefix is a provider

    >>> assert not is_provider('pdb')
    >>> assert is_provider('validatordb')
    """
    entry = get_resource(prefix)
    if entry is None:
        return False
    return entry.type == "provider"


def get_provides_for(prefix: str) -> Optional[str]:
    """Get the resource that the given prefix provides for, or return none if not a provider.

    :param prefix: The prefix to look up
    :returns: The prefix of the resource that the given prefix provides for, if it's a provider

    >>> assert get_provides_for('pdb') is None
    >>> assert 'pdb' == get_provides_for('validatordb')
    """
    entry = get_resource(prefix)
    if entry is None:
        return None
    return entry.provides


def get_license(prefix: str) -> Optional[str]:
    """Get the license for the resource.

    :param prefix: The prefix to look up
    :returns: The license of the resource (normalized) if available

    >>> assert get_provides_for('pdb') is None
    >>> assert 'pdb' == get_provides_for('validatordb')
    """
    for metaprefix in ("obofoundry", "ols"):
        license_value = _remap_license(get_external(prefix, metaprefix).get("license"))
        if license_value is not None:
            return license_value
    return None


def _remap_license(k: Optional[str]) -> Optional[str]:
    if k is None:
        return None
    return LICENSES.get(k, k)


def parse_curie(curie: str) -> Union[Tuple[str, str], Tuple[None, None]]:
    """Parse a CURIE, normalizing the prefix and identifier if necessary.

    :param curie: A compact URI (CURIE) in the form of <prefix:identifier>
    :returns: A tuple of the prefix, identifier. If not parsable, returns a tuple of None, None

    >>> parse_curie('pdb:1234')
    ('pdb', '1234')

    Address banana problem
    >>> parse_curie('go:GO:1234')
    ('go', '1234')
    >>> parse_curie('go:go:1234')
    ('go', '1234')
    >>> parse_curie('go:1234')
    ('go', '1234')

    Address banana problem with OBO banana
    >>> parse_curie('fbbt:FBbt:1234')
    ('fbbt', '1234')
    >>> parse_curie('fbbt:fbbt:1234')
    ('fbbt', '1234')
    >>> parse_curie('fbbt:1234')
    ('fbbt', '1234')

    Address banana problem with explit banana
    >>> parse_curie('go.ref:GO_REF:1234')
    ('go.ref', '1234')
    >>> parse_curie('go.ref:1234')
    ('go.ref', '1234')
    """
    try:
        prefix, identifier = curie.split(":", 1)
    except ValueError:
        return None, None
    return normalize_curie(prefix, identifier)


def normalize_curie(prefix: str, identifier: str) -> Union[Tuple[str, str], Tuple[None, None]]:
    """Normalize a prefix/identifier pair.

    :param prefix: The prefix in the CURIE
    :param identifier: The identifier in the CURIE
    :return: A normalized prefix/identifier pair, conforming to Bioregistry standards. This means no redundant
        prefixes or bananas, all lowercase.
    """
    norm_prefix = normalize_prefix(prefix)
    if not norm_prefix:
        return None, None

    banana = get_banana(prefix)
    if banana is not None and identifier.startswith(f"{banana}:"):
        identifier = identifier[len(banana) + 1 :]
    # remove redundant prefix
    elif identifier.casefold().startswith(f"{prefix.casefold()}:"):
        identifier = identifier[len(prefix) + 1 :]

    return norm_prefix, identifier


def normalize_prefix(prefix: str) -> Optional[str]:
    """Get the normalized prefix, or return None if not registered.

    :param prefix: The prefix to normalize, which could come from Bioregistry,
        OBO Foundry, OLS, or any of the curated synonyms in the Bioregistry
    :returns: The canonical Bioregistry prefix, it could be looked up. This
        will usually take precedence: MIRIAM, OBO Foundry / OLS, Custom except
        in a few cases, such as NCBITaxon.

    This works for synonym prefixes, like:

    >>> assert 'ncbitaxon' == normalize_prefix('taxonomy')

    This works for common mistaken prefixes, like:

    >>> assert 'pubchem.compound' == normalize_prefix('pubchem')

    This works for prefixes that are often written many ways, like:

    >>> assert 'eccode' == normalize_prefix('ec-code')
    >>> assert 'eccode' == normalize_prefix('EC_CODE')
    """
    return _synonym_to_canonical().get(prefix)


def _norm(s: str) -> str:
    """Normalize a string for dictionary key usage."""
    rv = s.casefold().lower()
    for x in " .-_./":
        rv = rv.replace(x, "")
    return rv


class NormDict(dict):
    def __setitem__(self, key: str, value: str) -> None:
        norm_key = _norm(key)
        if value is None:
            raise ValueError(f"Tried to add empty value for {key}/{norm_key}")
        if norm_key in self and self[norm_key] != value:
            raise KeyError(
                f"Tried to add {norm_key}/{value} when already had {norm_key}/{self[norm_key]}"
            )
        super().__setitem__(norm_key, value)

    def __getitem__(self, item: str) -> str:
        return super().__getitem__(_norm(item))

    def __contains__(self, item) -> bool:
        return super().__contains__(_norm(item))

    def get(self, key: str, default=None) -> str:
        return super().get(_norm(key), default)


@lru_cache(maxsize=1)
def _synonym_to_canonical() -> NormDict:
    """Return a mapping from several variants of each synonym to the canonical namespace."""
    norm_synonym_to_key = NormDict()

    for bioregistry_id, entry in read_registry().items():
        norm_synonym_to_key[bioregistry_id] = bioregistry_id
        for synonym in entry.synonyms or []:
            norm_synonym_to_key[synonym] = bioregistry_id

        for metaprefix in ("miriam", "ols", "obofoundry", "go"):
            external = entry.get_external(metaprefix)
            if external is None:
                continue
            external_prefix = external.get("prefix")
            if external_prefix is None:
                continue
            if external_prefix not in norm_synonym_to_key:
                logger.debug(f"[{bioregistry_id}] missing potential synonym: {external_prefix}")

    return norm_synonym_to_key


def get_version(prefix: str) -> Optional[str]:
    """Get the version."""
    norm_prefix = normalize_prefix(prefix)
    if norm_prefix is None:
        return None
    return get_versions().get(norm_prefix)


@lru_cache(maxsize=1)
def get_versions() -> Mapping[str, str]:
    """Get a map of prefixes to versions."""
    rv = {}
    for prefix in read_registry():
        version = get_external(prefix, "ols").get("version")
        if version is not None:
            rv[prefix] = version
    return rv


FORMATTERS: Mapping[str, Callable[[str], Optional[str]]] = {
    "bioregistry": _get_bioregistry_format,
    "obofoundry": get_obofoundry_formatter,
    "prefixcommons": get_prefixcommons_format,
    "miriam": get_miriam_format,
    "ols": get_ols_format,
}
