# -*- coding: utf-8 -*-

"""Utilities for normalizing prefixes."""

import logging
from functools import lru_cache
from typing import Any, Dict, List, Mapping, Optional, Set, Tuple, Union

from .resource_manager import manager
from .schema import Attributable, Resource

__all__ = [
    "get_resource",
    "get_name",
    "get_description",
    "get_preferred_prefix",
    "get_mappings",
    "get_synonyms",
    "get_pattern",
    "get_curie_pattern",
    "get_namespace_in_lui",
    "get_example",
    "has_no_terms",
    "is_deprecated",
    "is_proprietary",
    "get_contact",
    "get_contact_email",
    "get_contact_name",
    "get_contact_github",
    "get_contact_orcid",
    "get_homepage",
    "get_repository",
    "get_obo_download",
    "get_json_download",
    "get_owl_download",
    "get_version",
    "get_versions",
    "get_registry_map",
    "get_registry_invmap",
    "get_banana",
    "get_obo_health_url",
    # Ontology
    "get_provided_by",
    "get_provides_for",
    "get_part_of",
    "get_has_parts",
    "get_has_canonical",
    "get_canonical_for",
    "get_appears_in",
    "get_depends_on",
    # CURIE handling
    "normalize_prefix",
    "parse_curie",
    "normalize_parsed_curie",
    "normalize_curie",
]

logger = logging.getLogger(__name__)


def get_resource(prefix: str) -> Optional[Resource]:
    """Get the Bioregistry entry for the given prefix.

    :param prefix: The prefix to look up, which is normalized with :func:`normalize_prefix`
        before lookup in the Bioregistry
    :returns: The Bioregistry entry dictionary, which includes several keys cross-referencing
        other registries when available.
    """
    return manager.get_resource(prefix)


def get_name(prefix: str) -> Optional[str]:
    """Get the name for the given prefix, it it's available."""
    return manager.get_name(prefix)


def get_description(prefix: str, use_markdown: bool = False) -> Optional[str]:
    """Get the description for the given prefix, if available.

    :param prefix: The prefix to lookup.
    :param use_markdown: Should :mod:`markupsafe` and :mod:`markdown` wrap the description
        string
    :returns: The description, if available.
    """
    entry = get_resource(prefix)
    if entry is None:
        return None
    return entry.get_description(use_markdown=use_markdown)


def get_preferred_prefix(prefix: str) -> Optional[str]:
    """Get the preferred prefix (e.g., with stylization) if it exists.

    :param prefix: The prefix to lookup.
    :returns: The preferred prefix, if annotated in the Bioregistry or OBO Foundry.

    No preferred prefix annotation, defaults to normalized prefix
    >>> get_preferred_prefix("rhea")
    None

    Preferred prefix defined in the Bioregistry
    >>> get_preferred_prefix("wb")
    'WormBase'

    Preferred prefix defined in the OBO Foundry
    >>> get_preferred_prefix("fbbt")
    'FBbt'

    Preferred prefix from the OBO Foundry overridden by the Bioregistry
    (see also https://github.com/OBOFoundry/OBOFoundry.github.io/issues/1559)
    >>> get_preferred_prefix("dpo")
    'DPO'
    """
    return manager.get_preferred_prefix(prefix)


def get_mappings(prefix: str) -> Optional[Mapping[str, str]]:
    """Get the mappings to external registries, if available."""
    entry = get_resource(prefix)
    if entry is None:
        return None
    return entry.get_mappings()


def get_synonyms(prefix: str) -> Optional[Set[str]]:
    """Get the synonyms for a given prefix, if available."""
    return manager.get_synonyms(prefix)


def get_pattern(prefix: str) -> Optional[str]:
    """Get the pattern for the given prefix, if it's available.

    :param prefix: The prefix to look up, which is normalized with :func:`normalize_prefix`
        before lookup in the Bioregistry
    :returns: The pattern for the prefix, if it is available, using the following order of preference:
        1. Custom
        2. MIRIAM
        3. Wikidata
    """
    return manager.get_pattern(prefix)


def get_namespace_in_lui(prefix: str) -> Optional[bool]:
    """Check if the namespace should appear in the LUI."""
    entry = get_resource(prefix)
    if entry is None:
        return None
    return entry.get_namespace_in_lui()


def get_appears_in(prefix: str) -> Optional[List[str]]:
    """Return a list of resources that this resources (has been annotated to) depends on.

    This is complementary to :func:`get_depends_on`.

    :param prefix: The prefix to look up
    :returns: The list of resources this prefix has been annotated to appear in. This
        list could be incomplete, since curation of these fields can easily get out
        of sync with curation of the resource itself. However, false positives should
        be pretty rare.

    >>> import bioregistry
    >>> assert "bfo" not in bioregistry.get_appears_in("foodon")
    >>> assert "fobi" in bioregistry.get_appears_in("foodon")
    """
    return manager.get_appears_in(prefix)


def get_depends_on(prefix: str) -> Optional[List[str]]:
    """Return a list of resources that this resources (has been annotated to) depends on.

    This is complementary to :func:`get_appears_in`.

    :param prefix: The prefix to look up
    :returns: The list of resources this prefix has been annotated to depend on. This
        list could be incomplete, since curation of these fields can easily get out
        of sync with curation of the resource itself. However, false positives should
        be pretty rare.

    >>> import bioregistry
    >>> assert "bfo" in bioregistry.get_depends_on("foodon")
    >>> assert "fobi" not in bioregistry.get_depends_on("foodon")
    """
    return manager.get_depends_on(prefix)


def get_has_canonical(prefix: str) -> Optional[str]:
    """Get the canonical prefix.

    If two (or more) stand-alone resources both provide for the same
    semantic space, but none of them have a first-party claim to the
    semantic space, then the ``has_canonical`` relationship is used
    to choose a preferred prefix. This is different than the
    ``provides``, relationship, which is appropriate when it's obvious
    that one resource has a full claim to the semantic space.

    :param prefix: The prefix to lookup.
    :returns: The canonical prefix for this one, if one is annotated.
        This is the inverse of :func:`get_canonical_for`.

    >>> get_has_canonical("refseq")
    'ncbiprotein'
    >>> get_has_canonical("chebi")
    None
    """
    return manager.get_has_canonical(prefix)


def get_canonical_for(prefix: str) -> Optional[List[str]]:
    """Get the prefixes for which this is annotated as canonical.

    :param prefix: The prefix to lookup.
    :returns: The prefixes for which this is annotated as canonical.
        This is the inverse of :func:`get_has_canonical`.

    >>> "refseq" in get_canonical_for("ncbiprotein")
    True
    >>> get_canonical_for("chebi")
    []
    """
    return manager.get_canonical_for(prefix)


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
    entry = manager.get_resource(prefix)
    if entry is None:
        return None
    return entry.get_identifiers_org_prefix()


def get_n2t_prefix(prefix: str) -> Optional[str]:
    """Get the name-to-thing prefix if available.

    :param prefix: The prefix to lookup.
    :returns: The Name-to-Thing prefix corresponding to the prefix, if mappable.

    >>> import bioregistry
    >>> bioregistry.get_n2t_prefix('chebi')
    'chebi'
    >>> bioregistry.get_n2t_prefix('ncbitaxon')
    'taxonomy'
    >>> assert bioregistry.get_n2t_prefix('MONDO') is None
    """
    return manager.get_mapped_prefix(prefix, "n2t")


def get_wikidata_prefix(prefix: str) -> Optional[str]:
    """Get the wikidata prefix if available.

    :param prefix: The prefix to lookup.
    :returns: The Wikidata prefix (i.e., property identifier) corresponding to the prefix, if mappable.

    >>> get_wikidata_prefix('chebi')
    'P683'
    >>> get_wikidata_prefix('ncbitaxon')
    'P685'
    """
    return manager.get_mapped_prefix(prefix, "wikidata")


def get_bioportal_prefix(prefix: str) -> Optional[str]:
    """Get the BioPortal prefix if available.

    :param prefix: The prefix to lookup.
    :returns: The BioPortal prefix corresponding to the prefix, if mappable.

    >>> get_bioportal_prefix("chebi")
    'CHEBI'
    >>> get_bioportal_prefix("uniprot")
    None
    >>> get_bioportal_prefix("nope")
    None
    """
    return manager.get_mapped_prefix(prefix, "bioportal")


def get_obofoundry_prefix(prefix: str) -> Optional[str]:
    """Get the OBO Foundry prefix if available."""
    entry = get_resource(prefix)
    if entry is None:
        return None
    return entry.get_obofoundry_prefix()


def get_registry_map(metaprefix: str) -> Dict[str, str]:
    """Get a mapping from the Bioregistry prefixes to prefixes in another registry."""
    return manager.get_registry_map(metaprefix)


def get_registry_invmap(metaprefix: str) -> Dict[str, str]:
    """Get a mapping from the external registry prefixes to Bioregistry prefixes."""
    return manager.get_registry_invmap(metaprefix)


def get_obofoundry_uri_prefix(prefix: str) -> Optional[str]:
    """Get the URI prefix for an OBO Foundry entry.

    :param prefix: The prefix to lookup.
    :returns: The OBO PURL URI prefix corresponding to the prefix, if mappable.

    >>> import bioregistry
    >>> bioregistry.get_obofoundry_uri_prefix('go')  # standard
    'http://purl.obolibrary.org/obo/GO_'
    >>> bioregistry.get_obofoundry_uri_prefix('ncbitaxon')  # mixed case
    'http://purl.obolibrary.org/obo/NCBITaxon_'
    >>> assert bioregistry.get_obofoundry_uri_prefix('sty') is None
    """
    entry = get_resource(prefix)
    if entry is None:
        return None
    return entry.get_obofoundry_uri_prefix()


def get_ols_prefix(prefix: str) -> Optional[str]:
    """Get the OLS prefix if available."""
    entry = get_resource(prefix)
    if entry is None:
        return None
    return entry.get_ols_prefix()


def get_fairsharing_prefix(prefix: str) -> Optional[str]:
    """Get the FAIRSharing prefix if available.

    :param prefix: The prefix to lookup.
    :returns: The FAIRSharing prefix corresponding to the prefix, if mappable.

    >>> get_fairsharing_prefix("genbank")
    'FAIRsharing.9kahy4'
    """
    return manager.get_mapped_prefix(prefix, "fairsharing")


def get_scholia_prefix(prefix: str) -> Optional[str]:
    """Get the Scholia prefix if available.

    :param prefix: The prefix to lookup.
    :returns: The Scholia prefix corresponding to the prefix, if mappable.

    >>> get_scholia_prefix("pubmed")
    'pubmed'
    >>> get_scholia_prefix("pdb")
    None
    """
    entry = get_resource(prefix)
    if entry is None:
        return None
    return entry.get_scholia_prefix()


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

    Banana inferred for OBO Foundry ontology
    >>> get_banana('chebi')
    'CHEBI'

    No banana, no namespace in LUI
    >>> assert get_banana('pdb') is None
    """
    entry = get_resource(prefix)
    if entry is None:
        return None
    return entry.get_banana()


def get_default_format(prefix: str) -> Optional[str]:
    """Get the default, first-party URI prefix.

    :param prefix: The prefix to lookup.
    :returns: The first-party URI prefix string, if available.

    >>> import bioregistry
    >>> bioregistry.get_default_format('ncbitaxon')
    'https://www.ncbi.nlm.nih.gov/Taxonomy/Browser/wwwtax.cgi?mode=Info&id=$1'
    >>> bioregistry.get_default_format('go')
    'http://amigo.geneontology.org/amigo/term/GO:$1'
    >>> assert bioregistry.get_default_format('nope') is None
    """
    entry = get_resource(prefix)
    if entry is None:
        return None
    return entry.get_default_format()


def get_miriam_uri_prefix(prefix: str) -> Optional[str]:
    """Get the URI prefix for a MIRIAM entry.

    :param prefix: The prefix to lookup.
    :returns: The Identifiers.org/MIRIAM URI prefix, if available.

    >>> import bioregistry
    >>> bioregistry.get_miriam_uri_prefix('ncbitaxon')
    'https://identifiers.org/taxonomy:'
    >>> bioregistry.get_miriam_uri_prefix('go')
    'https://identifiers.org/GO:'
    >>> assert bioregistry.get_miriam_uri_prefix('sty') is None
    """
    resource = get_resource(prefix)
    if resource is None:
        return None
    return resource.get_miriam_uri_prefix()


def get_miriam_uri_format(prefix: str) -> Optional[str]:
    """Get the URI format for a MIRIAM entry.

    :param prefix: The prefix to lookup.
    :returns: The Identifiers.org/MIRIAM URI format string, if available.

    >>> import bioregistry
    >>> bioregistry.get_miriam_uri_format('ncbitaxon')
    'https://identifiers.org/taxonomy:$1'
    >>> bioregistry.get_miriam_uri_format('go')
    'https://identifiers.org/GO:$1'
    >>> assert bioregistry.get_miriam_uri_format('sty') is None
    """
    resource = get_resource(prefix)
    if resource is None:
        return None
    return resource.get_miriam_uri_format()


def get_obofoundry_uri_format(prefix: str) -> Optional[str]:
    """Get the OBO Foundry URI format for this entry, if possible.

    :param prefix: The prefix to lookup.
    :returns: The OBO PURL format string, if available.

    >>> import bioregistry
    >>> bioregistry.get_obofoundry_uri_format('go')  # standard
    'http://purl.obolibrary.org/obo/GO_$1'
    >>> bioregistry.get_obofoundry_uri_format('ncbitaxon')  # mixed case
    'http://purl.obolibrary.org/obo/NCBITaxon_$1'
    >>> assert bioregistry.get_obofoundry_uri_format('sty') is None
    """
    resource = get_resource(prefix)
    if resource is None:
        return None
    return resource.get_obofoundry_uri_format()


def get_ols_uri_prefix(prefix: str) -> Optional[str]:
    """Get the URI format for an OLS entry.

    :param prefix: The prefix to lookup.
    :returns: The OLS format string, if available.

    .. warning:: This doesn't have a normal form, so it only works for OBO Foundry at the moment.

    >>> import bioregistry
    >>> bioregistry.get_ols_uri_prefix('go')  # standard
    'https://www.ebi.ac.uk/ols/ontologies/go/terms?iri=http://purl.obolibrary.org/obo/GO_'
    >>> bioregistry.get_ols_uri_prefix('ncbitaxon')  # mixed case
    'https://www.ebi.ac.uk/ols/ontologies/ncbitaxon/terms?iri=http://purl.obolibrary.org/obo/NCBITaxon_'
    >>> assert bioregistry.get_ols_uri_prefix('sty') is None
    """
    resource = get_resource(prefix)
    if resource is None:
        return None
    return resource.get_ols_uri_prefix()


def get_ols_uri_format(prefix: str) -> Optional[str]:
    """Get the URI format for an OLS entry.

    :param prefix: The prefix to lookup.
    :returns: The OLS format string, if available.

    .. warning:: This doesn't have a normal form, so it only works for OBO Foundry at the moment.

    >>> import bioregistry
    >>> bioregistry.get_ols_uri_format('go')  # standard
    'https://www.ebi.ac.uk/ols/ontologies/go/terms?iri=http://purl.obolibrary.org/obo/GO_$1'
    >>> bioregistry.get_ols_uri_format('ncbitaxon')  # mixed case
    'https://www.ebi.ac.uk/ols/ontologies/ncbitaxon/terms?iri=http://purl.obolibrary.org/obo/NCBITaxon_$1'
    >>> assert bioregistry.get_ols_uri_format('sty') is None
    """
    resource = get_resource(prefix)
    if resource is None:
        return None
    return resource.get_ols_uri_format()


def get_prefixcommons_uri_format(prefix: str) -> Optional[str]:
    """Get the URI format for a Prefix Commons entry.

    :param prefix: The prefix to lookup.
    :returns: The Prefix Commons URI format string, if available.

    >>> import bioregistry
    >>> bioregistry.get_prefixcommons_uri_format('hgmd')
    'http://www.hgmd.cf.ac.uk/ac/gene.php?gene=$1'
    """
    resource = get_resource(prefix)
    if resource is None:
        return None
    return resource.get_prefixcommons_uri_format()


def get_external(prefix: str, metaprefix: str) -> Mapping[str, Any]:
    """Get the external data for the entry."""
    return manager.get_external(prefix, metaprefix)


def get_example(prefix: str) -> Optional[str]:
    """Get an example identifier, if it's available."""
    return manager.get_example(prefix)


def has_no_terms(prefix: str) -> bool:
    """Check if the prefix is specifically noted to not have terms."""
    return manager.has_no_terms(prefix)


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
    return manager.is_deprecated(prefix)


def get_contact(prefix: str) -> Optional[Attributable]:
    """Return the contact, if available.

    :param prefix: The prefix to lookup
    :returns: The resource's contact, if it is available.
    """
    entry = get_resource(prefix)
    if entry is None:
        return None
    return entry.get_contact()


def get_contact_email(prefix: str) -> Optional[str]:
    """Return the contact email, if available.

    :param prefix: The prefix to lookup
    :returns: The resource's contact email address, if it is available.

    >>> import bioregistry
    >>> bioregistry.get_contact_email('bioregistry')  # from bioregistry curation
    'cthoyt@gmail.com'
    >>> bioregistry.get_contact_email('chebi')
    'amalik@ebi.ac.uk'
    >>> assert bioregistry.get_contact_email('pass2') is None  # dead resource
    """
    entry = get_resource(prefix)
    if entry is None:
        return None
    return entry.get_contact_email()


def get_contact_github(prefix: str) -> Optional[str]:
    """Return the contact GitHub, if available.

    :param prefix: The prefix to lookup
    :returns: The resource's contact GitHub handle, if it is available.
    """
    entry = get_resource(prefix)
    if entry is None:
        return None
    return entry.get_contact_github()


def get_contact_orcid(prefix: str) -> Optional[str]:
    """Return the contact ORCiD, if available.

    :param prefix: The prefix to lookup
    :returns: The resource's contact ORCiD, if it is available.
    """
    entry = get_resource(prefix)
    if entry is None:
        return None
    return entry.get_contact_orcid()


def get_contact_name(prefix: str) -> Optional[str]:
    """Return the contact name, if available.

    :param prefix: The prefix to lookup
    :returns: The resource's contact name, if it is available.

    >>> import bioregistry
    >>> bioregistry.get_contact_name('bioregistry')  # from bioregistry curation
    'Charles Tapley Hoyt'
    >>> bioregistry.get_contact_name('chebi')
    'Adnan Malik'
    >>> assert bioregistry.get_contact_name('pass2') is None  # dead resource
    """
    entry = get_resource(prefix)
    if entry is None:
        return None
    return entry.get_contact_name()


def get_homepage(prefix: str) -> Optional[str]:
    """Return the homepage, if available."""
    entry = get_resource(prefix)
    if entry is None:
        return None
    return entry.get_homepage()


def get_repository(prefix: str) -> Optional[str]:
    """Return the repository, if available."""
    entry = get_resource(prefix)
    if entry is None:
        return None
    return entry.get_repository()


def get_obo_download(prefix: str) -> Optional[str]:
    """Get the download link for the latest OBO file."""
    entry = get_resource(prefix)
    if entry is None:
        return None
    return entry.get_download_obo()


def get_json_download(prefix: str) -> Optional[str]:
    """Get the download link for the latest OBOGraph JSON file."""
    entry = get_resource(prefix)
    if entry is None:
        return None
    return entry.get_download_obograph()


def get_owl_download(prefix: str) -> Optional[str]:
    """Get the download link for the latest OWL file."""
    entry = get_resource(prefix)
    if entry is None:
        return None
    return entry.get_download_owl()


def get_provides_for(prefix: str) -> Optional[str]:
    """Get the resource that the given prefix provides for, or return none if not a provider.

    :param prefix: The prefix to look up
    :returns: The prefix of the resource that the given prefix provides for, if it's a provider.
        This is the inverse of :func:`get_provided_by`.

    >>> assert get_provides_for('pdb') is None
    >>> assert 'pdb' == get_provides_for('validatordb')
    """
    return manager.get_provides_for(prefix)


def get_provided_by(prefix: str) -> Optional[List[str]]:
    """Get the resources that provide for the given prefix, or return none if the prefix can't be looked up.

    :param prefix: The prefix to look up
    :returns: The prefixes of the resources that provide for the given prefix. This
        is the inverse of :func:`get_provides_for`.

    >>> get_provides_for("validatordb")
    'pdb'
    """
    return manager.get_provided_by(prefix)


def get_part_of(prefix: str) -> Optional[str]:
    """Get the parent resource.

    :param prefix: The prefix to look up
    :returns: The prefixes of the parent resource for this prefix, if one is annotated. This
        is the inverse of :func:`get_has_parts`.

    >>> assert 'chembl' in get_part_of('chembl.compound')
    """
    return manager.get_part_of(prefix)


def get_has_parts(prefix: str) -> Optional[List[str]]:
    """Get children resources.

    :param prefix: The prefix to look up
    :returns: The prefixes of resource for which this prefix is the parent. This
        is the inverse of :func:`get_has_parts`.

    >>> assert 'chembl.compound' in get_has_parts('chembl')
    """
    return manager.get_has_parts(prefix)


def get_license(prefix: str) -> Optional[str]:
    """Get the license for the resource.

    :param prefix: The prefix to look up
    :returns: The license of the resource (normalized) if available
    """
    entry = get_resource(prefix)
    if entry is None:
        return None
    return entry.get_license()


def is_proprietary(prefix: str) -> Optional[bool]:
    """Get if the prefix is proprietary.

    :param prefix: The prefix to look up
    :returns: If the prefix corresponds to a proprietary resource. Assume false if not annotated explicitly

    >>> assert is_proprietary('eurofir')
    >>> assert not is_proprietary('chebi')
    """
    entry = get_resource(prefix)
    if entry is None:
        return None
    if entry.proprietary is None:
        return False
    return entry.proprietary


def parse_curie(curie: str, sep: str = ":") -> Union[Tuple[str, str], Tuple[None, None]]:
    """Parse a CURIE, normalizing the prefix and identifier if necessary.

    :param curie: A compact URI (CURIE) in the form of <prefix:identifier>
    :param sep: The separator for the CURIE. Defaults to the colon ":" however the slash
        "/" is sometimes used in Identifiers.org and the underscore "_" is used for OBO PURLs.
    :returns: A tuple of the prefix, identifier. If not parsable, returns a tuple of None, None

    The algorithm for parsing a CURIE is very simple: it splits the string on the leftmost occurrence
    of the separator (usually a colon ":" unless specified otherwise). The left part is the prefix,
    and the right part is the identifier.

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

    Parse OBO PURL curies
    >>> parse_curie('GO_1234', sep="_")
    ('go', '1234')
    """
    return manager.parse_curie(curie, sep=sep)


def normalize_parsed_curie(
    prefix: str, identifier: str
) -> Union[Tuple[str, str], Tuple[None, None]]:
    """Normalize a prefix/identifier pair.

    :param prefix: The prefix in the CURIE
    :param identifier: The identifier in the CURIE
    :return: A normalized prefix/identifier pair, conforming to Bioregistry standards. This means no redundant
        prefixes or bananas, all lowercase.
    """
    return manager.normalize_parsed_curie(prefix, identifier)


def normalize_curie(curie: str, sep: str = ":") -> Optional[str]:
    """Normalize a CURIE.

    :param curie: A compact URI (CURIE) in the form of <prefix:identifier>
    :param sep: The separator for the CURIE. Defaults to the colon ":" however the slash
        "/" is sometimes used in Identifiers.org and the underscore "_" is used for OBO PURLs.
    :return: A normalized CURIE, if possible using the colon as a separator

    >>> normalize_curie('pdb:1234')
    'pdb:1234'

    Fix commonly mistaken prefix
    >>> normalize_curie('pubchem:1234')
    'pubchem.compound:1234'

    Address banana problem
    >>> normalize_curie('GO:GO:1234')
    'go:1234'
    >>> normalize_curie('go:GO:1234')
    'go:1234'
    >>> normalize_curie('go:go:1234')
    'go:1234'
    >>> normalize_curie('go:1234')
    'go:1234'

    Address banana problem with OBO banana
    >>> normalize_curie('fbbt:FBbt:1234')
    'fbbt:1234'
    >>> normalize_curie('fbbt:fbbt:1234')
    'fbbt:1234'
    >>> normalize_curie('fbbt:1234')
    'fbbt:1234'

    Address banana problem with explit banana
    >>> normalize_curie('go.ref:GO_REF:1234')
    'go.ref:1234'
    >>> normalize_curie('go.ref:1234')
    'go.ref:1234'

    Parse OBO PURL curies
    >>> normalize_curie('GO_1234', sep="_")
    'go:1234'
    """
    return manager.normalize_curie(curie, sep=sep)


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
    return manager.normalize_prefix(prefix)


def get_version(prefix: str) -> Optional[str]:
    """Get the version."""
    norm_prefix = normalize_prefix(prefix)
    if norm_prefix is None:
        return None
    return get_versions().get(norm_prefix)


@lru_cache(maxsize=1)
def get_versions() -> Mapping[str, str]:
    """Get a map of prefixes to versions."""
    return manager.get_versions()


def get_curie_pattern(prefix: str) -> Optional[str]:
    """Get the CURIE pattern for this resource.

    :param prefix: The prefix to look up
    :return: The regular expression pattern to match CURIEs against
    """
    return manager.get_curie_pattern(prefix)


def get_license_conflicts():
    """Get license conflicts."""
    return manager.get_license_conflicts()


SHIELDS_BASE = "https://img.shields.io/badge/dynamic"
CH_BASE = "https://cthoyt.com/obo-community-health"
HEALTH_BASE = "https://github.com/cthoyt/obo-community-health/raw/main/data/data.json"
EXTRAS = f"%20Community%20Health%20Score&link={CH_BASE}"


def get_obo_health_url(prefix: str) -> Optional[str]:
    """Get the OBO community health badge."""
    obo_prefix = manager.get_mapped_prefix(prefix, "obofoundry")
    if obo_prefix is None:
        return None
    obo_pp = manager.get_preferred_prefix(prefix)
    return f"{SHIELDS_BASE}/json?url={HEALTH_BASE}&query=$.{obo_prefix.lower()}.score&label={obo_pp}{EXTRAS}"
