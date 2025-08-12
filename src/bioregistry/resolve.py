"""Utilities for normalizing prefixes."""

from __future__ import annotations

import logging
import typing
from collections.abc import Mapping
from functools import lru_cache
from typing import Any, Literal, overload

import curies

from .resource_manager import MetaresourceAnnotatedValue, manager
from .schema import Attributable, Resource

__all__ = [
    "add_resource",
    "count_mappings",
    "get_appears_in",
    "get_banana",
    "get_canonical_for",
    "get_contact",
    "get_contact_email",
    "get_contact_github",
    "get_contact_name",
    "get_contact_orcid",
    "get_converter",
    "get_curie_pattern",
    "get_depends_on",
    "get_description",
    "get_example",
    "get_has_canonical",
    "get_has_parts",
    "get_homepage",
    "get_json_download",
    "get_keywords",
    "get_logo",
    "get_mailing_list",
    "get_mappings",
    "get_name",
    "get_namespace_in_lui",
    "get_obo_context_prefix_map",
    "get_obo_download",
    "get_obo_health_url",
    "get_owl_download",
    "get_part_of",
    "get_parts_collections",
    "get_pattern",
    "get_preferred_prefix",
    # Ontology
    "get_provided_by",
    "get_provides_for",
    "get_rdf_download",
    "get_registry_invmap",
    # Registry-level functions
    "get_registry_map",
    "get_repository",
    "get_resource",
    "get_synonyms",
    "get_version",
    "get_versions",
    "has_no_terms",
    "is_deprecated",
    "is_novel",
    "is_obo_foundry",
    "is_proprietary",
]

logger = logging.getLogger(__name__)


# docstr-coverage:excused `overload`
@overload
def get_resource(prefix: str, *, strict: Literal[True] = True) -> Resource: ...


# docstr-coverage:excused `overload`
@overload
def get_resource(prefix: str, *, strict: Literal[False] = False) -> Resource | None: ...


def get_resource(prefix: str, *, strict: bool = False) -> Resource | None:
    """Get the Bioregistry entry for the given prefix.

    :param prefix: The prefix to look up, which is normalized with :func:`normalize_prefix`
        before lookup in the Bioregistry
    :param strict: If true, requires the prefix to be valid or raise an exveption
    :returns: The Bioregistry entry dictionary, which includes several keys cross-referencing
        other registries when available.
    """
    if strict:
        return manager.get_resource(prefix, strict=True)
    return manager.get_resource(prefix, strict=False)


# docstr-coverage:excused `overload`
@overload
def get_name(
    prefix: str, *, provenance: Literal[False] = False, strict: Literal[True] = True
) -> str: ...


# docstr-coverage:excused `overload`
@overload
def get_name(
    prefix: str, *, provenance: Literal[True] = True, strict: Literal[True] = True
) -> MetaresourceAnnotatedValue[str]: ...


# docstr-coverage:excused `overload`
@overload
def get_name(
    prefix: str, *, provenance: Literal[False] = False, strict: Literal[False] = False
) -> None | str: ...


# docstr-coverage:excused `overload`
@overload
def get_name(
    prefix: str, *, provenance: Literal[True] = True, strict: Literal[False] = False
) -> None | MetaresourceAnnotatedValue[str]: ...


def get_name(
    prefix: str, *, provenance: bool = False, strict: bool = False
) -> str | MetaresourceAnnotatedValue[str] | None:
    """Get the name for the given prefix, if it's available."""
    if provenance:
        if strict:
            return manager.get_name(prefix, provenance=True, strict=True)
        else:
            return manager.get_name(prefix, provenance=True, strict=False)
    if strict:
        return manager.get_name(prefix, provenance=False, strict=True)
    return manager.get_name(prefix, provenance=False, strict=False)


def get_description(prefix: str, *, use_markdown: bool = False) -> str | None:
    """Get the description for the given prefix, if available.

    :param prefix: The prefix to lookup.
    :param use_markdown: Should :mod:`markupsafe` and :mod:`markdown` wrap the description
        string
    :returns: The description, if available.
    """
    return manager.get_description(prefix, use_markdown=use_markdown)


def get_preferred_prefix(prefix: str) -> str | None:
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


def get_mappings(prefix: str) -> Mapping[str, str] | None:
    """Get the mappings to external registries, if available."""
    entry = get_resource(prefix)
    if entry is None:
        return None
    return entry.get_mappings()


def count_mappings() -> typing.Counter[str]:
    """Count the mappings for each registry."""
    return manager.count_mappings()


def get_synonyms(prefix: str) -> set[str] | None:
    """Get the synonyms for a given prefix, if available."""
    return manager.get_synonyms(prefix)


def get_keywords(prefix: str) -> list[str] | None:
    """Return the keywords, if available."""
    return manager.get_keywords(prefix)


def get_pattern(prefix: str) -> str | None:
    """Get the pattern for the given prefix, if it's available.

    :param prefix: The prefix to look up, which is normalized with :func:`normalize_prefix`
        before lookup in the Bioregistry
    :returns: The pattern for the prefix, if it is available, using the following order of preference:
        1. Custom
        2. MIRIAM
        3. Wikidata
    """
    return manager.get_pattern(prefix)


def get_namespace_in_lui(
    prefix: str, *, provenance: bool = False
) -> bool | MetaresourceAnnotatedValue[bool] | None:
    """Check if the namespace should appear in the LUI."""
    if provenance:
        return manager.get_namespace_in_lui(prefix, provenance=True)
    return manager.get_namespace_in_lui(prefix, provenance=False)


def get_appears_in(prefix: str) -> list[str] | None:
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


def get_depends_on(prefix: str) -> list[str] | None:
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


def get_has_canonical(prefix: str) -> str | None:
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


def get_canonical_for(prefix: str) -> list[str] | None:
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


def get_identifiers_org_prefix(prefix: str) -> str | None:
    """Get the identifiers.org prefix if available.

    :param prefix: The prefix to lookup.
    :returns: The Identifiers.org/MIRIAM prefix corresponding to the prefix, if mappable.

    >>> import bioregistry
    >>> bioregistry.get_identifiers_org_prefix("chebi")
    'chebi'
    >>> bioregistry.get_identifiers_org_prefix("ncbitaxon")
    'taxonomy'
    >>> assert bioregistry.get_identifiers_org_prefix("MONDO") is None
    """
    entry = manager.get_resource(prefix)
    if entry is None:
        return None
    return entry.get_identifiers_org_prefix()


def get_n2t_prefix(prefix: str) -> str | None:
    """Get the name-to-thing prefix if available.

    :param prefix: The prefix to lookup.
    :returns: The Name-to-Thing prefix corresponding to the prefix, if mappable.

    >>> import bioregistry
    >>> bioregistry.get_n2t_prefix("chebi")
    'chebi'
    >>> bioregistry.get_n2t_prefix("ncbitaxon")
    'taxonomy'
    >>> assert bioregistry.get_n2t_prefix("MONDO") is None
    """
    return manager.get_mapped_prefix(prefix, "n2t")


def get_wikidata_prefix(prefix: str) -> str | None:
    """Get the wikidata prefix if available.

    :param prefix: The prefix to lookup.
    :returns: The Wikidata prefix (i.e., property identifier) corresponding to the prefix, if mappable.

    >>> get_wikidata_prefix("chebi")
    'P683'
    >>> get_wikidata_prefix("ncbitaxon")
    'P685'
    """
    return manager.get_mapped_prefix(prefix, "wikidata")


def get_bioportal_prefix(prefix: str) -> str | None:
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


def get_obofoundry_prefix(prefix: str) -> str | None:
    """Get the OBO Foundry prefix if available."""
    entry = get_resource(prefix)
    if entry is None:
        return None
    return entry.get_obofoundry_prefix()


def get_registry_map(metaprefix: str) -> dict[str, str]:
    """Get a mapping from the Bioregistry prefixes to prefixes in another registry."""
    return manager.get_registry_map(metaprefix)


def get_registry_invmap(metaprefix: str, **kwargs: Any) -> dict[str, str]:
    """Get a mapping from the external registry prefixes to Bioregistry prefixes."""
    return manager.get_registry_invmap(metaprefix, **kwargs)


def get_obofoundry_uri_prefix(prefix: str) -> str | None:
    """Get the URI prefix for an OBO Foundry entry.

    :param prefix: The prefix to lookup.
    :returns: The OBO PURL URI prefix corresponding to the prefix, if mappable.

    >>> import bioregistry
    >>> bioregistry.get_obofoundry_uri_prefix("go")  # standard
    'http://purl.obolibrary.org/obo/GO_'
    >>> bioregistry.get_obofoundry_uri_prefix("ncbitaxon")  # mixed case
    'http://purl.obolibrary.org/obo/NCBITaxon_'
    >>> assert bioregistry.get_obofoundry_uri_prefix("sty") is None
    """
    entry = get_resource(prefix)
    if entry is None:
        return None
    return entry.get_obofoundry_uri_prefix()


def get_ols_prefix(prefix: str) -> str | None:
    """Get the OLS prefix if available."""
    entry = get_resource(prefix)
    if entry is None:
        return None
    return entry.get_ols_prefix()


def get_fairsharing_prefix(prefix: str) -> str | None:
    """Get the FAIRSharing prefix if available.

    :param prefix: The prefix to lookup.
    :returns: The FAIRSharing prefix corresponding to the prefix, if mappable.

    >>> get_fairsharing_prefix("genbank")
    'FAIRsharing.9kahy4'
    """
    return manager.get_mapped_prefix(prefix, "fairsharing")


def get_banana(prefix: str) -> str | None:
    """Get the optional redundant prefix to go before an identifier.

    A "banana" is an embedded prefix that isn't actually part of the identifier.
    Usually this corresponds to the prefix itself, with some specific stylization
    such as in the case of FBbt. The banana does NOT include a colon ":" at the end

    :param prefix: The name of the prefix (possibly unnormalized)
    :return: The banana, if the prefix is valid and has an associated banana.

    Explicitly annotated banana
    >>> assert "GO_REF" == get_banana("go.ref")

    Banana imported through OBO Foundry
    >>> assert "GO" == get_banana("go")
    >>> assert "VariO" == get_banana("vario")

    Banana inferred for OBO Foundry ontology
    >>> get_banana("chebi")
    'CHEBI'

    No banana, no namespace in LUI
    >>> assert get_banana("pdb") is None
    """
    entry = get_resource(prefix)
    if entry is None:
        return None
    return entry.get_banana()


def get_default_format(prefix: str) -> str | None:
    """Get the default, first-party URI prefix.

    :param prefix: The prefix to lookup.
    :returns: The first-party URI prefix string, if available.

    >>> import bioregistry
    >>> bioregistry.get_default_format("ncbitaxon")
    'http://purl.obolibrary.org/obo/NCBITaxon_$1'
    >>> bioregistry.get_default_format("go")
    'http://purl.obolibrary.org/obo/GO_$1'
    >>> assert bioregistry.get_default_format("nope") is None
    """
    entry = get_resource(prefix)
    if entry is None:
        return None
    return entry.get_default_format()


def get_miriam_uri_prefix(prefix: str, **kwargs: Any) -> str | None:
    """Get the URI prefix for a MIRIAM entry.

    :param prefix: The prefix to lookup.
    :param kwargs: Keyword arguments to pass to :meth:`Resource.get_miriam_uri_prefix`
    :returns: The Identifiers.org/MIRIAM URI prefix, if available.

    >>> import bioregistry
    >>> bioregistry.get_miriam_uri_prefix("ncbitaxon")
    'https://identifiers.org/taxonomy:'
    >>> bioregistry.get_miriam_uri_prefix("go")
    'https://identifiers.org/GO:'
    >>> assert bioregistry.get_miriam_uri_prefix("sty") is None
    """
    resource = get_resource(prefix)
    if resource is None:
        return None
    return resource.get_miriam_uri_prefix(**kwargs)


def get_miriam_uri_format(prefix: str, **kwargs: Any) -> str | None:
    """Get the URI format for a MIRIAM entry.

    :param prefix: The prefix to lookup.
    :param kwargs: Keyword arguments to pass to :meth:`Resource.get_miriam_uri_format`
    :returns: The Identifiers.org/MIRIAM URI format string, if available.

    >>> import bioregistry
    >>> bioregistry.get_miriam_uri_format("ncbitaxon")
    'https://identifiers.org/taxonomy:$1'
    >>> bioregistry.get_miriam_uri_format("go")
    'https://identifiers.org/GO:$1'
    >>> assert bioregistry.get_miriam_uri_format("sty") is None
    """
    resource = get_resource(prefix)
    if resource is None:
        return None
    return resource.get_miriam_uri_format(**kwargs)


def get_obofoundry_uri_format(prefix: str) -> str | None:
    """Get the OBO Foundry URI format for this entry, if possible.

    :param prefix: The prefix to lookup.
    :returns: The OBO PURL format string, if available.

    >>> import bioregistry
    >>> bioregistry.get_obofoundry_uri_format("go")  # standard
    'http://purl.obolibrary.org/obo/GO_$1'
    >>> bioregistry.get_obofoundry_uri_format("ncbitaxon")  # mixed case
    'http://purl.obolibrary.org/obo/NCBITaxon_$1'
    >>> assert bioregistry.get_obofoundry_uri_format("sty") is None
    """
    resource = get_resource(prefix)
    if resource is None:
        return None
    return resource.get_obofoundry_uri_format()


def get_ols_uri_prefix(prefix: str) -> str | None:
    """Get the URI format for an OLS entry.

    :param prefix: The prefix to lookup.
    :returns: The OLS format string, if available.

    .. warning:: This doesn't have a normal form, so it only works for OBO Foundry at the moment.

    >>> import bioregistry
    >>> bioregistry.get_ols_uri_prefix("go")  # standard
    'https://www.ebi.ac.uk/ols/ontologies/go/terms?iri=http://purl.obolibrary.org/obo/GO_'
    >>> bioregistry.get_ols_uri_prefix("ncbitaxon")  # mixed case
    'https://www.ebi.ac.uk/ols/ontologies/ncbitaxon/terms?iri=http://purl.obolibrary.org/obo/NCBITaxon_'
    >>> assert bioregistry.get_ols_uri_prefix("sty") is None
    """
    resource = get_resource(prefix)
    if resource is None:
        return None
    return resource.get_ols_uri_prefix()


def get_ols_uri_format(prefix: str) -> str | None:
    """Get the URI format for an OLS entry.

    :param prefix: The prefix to lookup.
    :returns: The OLS format string, if available.

    .. warning:: This doesn't have a normal form, so it only works for OBO Foundry at the moment.

    >>> import bioregistry
    >>> bioregistry.get_ols_uri_format("go")  # standard
    'https://www.ebi.ac.uk/ols/ontologies/go/terms?iri=http://purl.obolibrary.org/obo/GO_$1'
    >>> bioregistry.get_ols_uri_format("ncbitaxon")  # mixed case
    'https://www.ebi.ac.uk/ols/ontologies/ncbitaxon/terms?iri=http://purl.obolibrary.org/obo/NCBITaxon_$1'
    >>> assert bioregistry.get_ols_uri_format("sty") is None
    """
    resource = get_resource(prefix)
    if resource is None:
        return None
    return resource.get_ols_uri_format()


def get_biocontext_uri_format(prefix: str) -> str | None:
    """Get the URI format for a BioContext entry.

    :param prefix: The prefix to lookup.
    :returns: The BioContext URI format string, if available.

    >>> import bioregistry
    >>> bioregistry.get_biocontext_uri_format("hgmd")
    'http://www.hgmd.cf.ac.uk/ac/gene.php?gene=$1'
    """
    resource = get_resource(prefix)
    if resource is None:
        return None
    return resource.get_biocontext_uri_format()


def get_prefixcommons_uri_format(prefix: str) -> str | None:
    """Get the URI format for a Prefix Commons entry.

    :param prefix: The prefix to lookup.
    :returns: The Prefix Commons URI format string, if available.

    >>> import bioregistry
    >>> bioregistry.get_prefixcommons_uri_format("antweb")
    'http://www.antweb.org/specimen.do?name=$1'
    """
    resource = get_resource(prefix)
    if resource is None:
        return None
    return resource.get_prefixcommons_uri_format()


def get_external(prefix: str, metaprefix: str) -> Mapping[str, Any]:
    """Get the external data for the entry."""
    return manager.get_external(prefix, metaprefix)


def get_example(prefix: str) -> str | None:
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
    >>> assert bioregistry.is_deprecated("imr")  # marked by OBO
    >>> assert bioregistry.is_deprecated("idomal")  # marked by OBO as inactive
    >>> assert bioregistry.is_deprecated("iro")  # marked by Bioregistry
    >>> assert bioregistry.is_deprecated("miriam.collection")  # marked by MIRIAM
    """
    return manager.is_deprecated(prefix)


def get_contact(prefix: str) -> Attributable | None:
    """Return the contact, if available.

    :param prefix: The prefix to lookup
    :returns: The resource's contact, if it is available.
    """
    entry = get_resource(prefix)
    if entry is None:
        return None
    return entry.get_contact()


def get_contact_email(prefix: str) -> str | None:
    """Return the contact email, if available.

    :param prefix: The prefix to lookup
    :returns: The resource's contact email address, if it is available.

    >>> import bioregistry
    >>> bioregistry.get_contact_email("bioregistry")  # from bioregistry curation
    'cthoyt@gmail.com'
    >>> bioregistry.get_contact_email("chebi")
    'amalik@ebi.ac.uk'
    >>> assert bioregistry.get_contact_email("pass2") is None  # dead resource
    """
    entry = get_resource(prefix)
    if entry is None:
        return None
    return entry.get_contact_email()


def get_contact_github(prefix: str) -> str | None:
    """Return the contact GitHub, if available.

    :param prefix: The prefix to lookup
    :returns: The resource's contact GitHub handle, if it is available.
    """
    entry = get_resource(prefix)
    if entry is None:
        return None
    return entry.get_contact_github()


def get_contact_orcid(prefix: str) -> str | None:
    """Return the contact ORCiD, if available.

    :param prefix: The prefix to lookup
    :returns: The resource's contact ORCiD, if it is available.
    """
    entry = get_resource(prefix)
    if entry is None:
        return None
    return entry.get_contact_orcid()


def get_contact_name(prefix: str) -> str | None:
    """Return the contact name, if available.

    :param prefix: The prefix to lookup
    :returns: The resource's contact name, if it is available.

    >>> import bioregistry
    >>> bioregistry.get_contact_name("bioregistry")  # from bioregistry curation
    'Charles Tapley Hoyt'
    >>> bioregistry.get_contact_name("chebi")
    'Adnan Malik'
    >>> assert bioregistry.get_contact_name("pass2") is None  # dead resource
    """
    entry = get_resource(prefix)
    if entry is None:
        return None
    return entry.get_contact_name()


def get_homepage(prefix: str) -> str | None:
    """Return the homepage, if available."""
    return manager.get_homepage(prefix)


def get_repository(prefix: str) -> str | None:
    """Return the repository, if available."""
    entry = get_resource(prefix)
    if entry is None:
        return None
    return entry.get_repository()


def get_obo_download(prefix: str) -> str | None:
    """Get the download link for the latest OBO file."""
    entry = get_resource(prefix)
    if entry is None:
        return None
    return entry.get_download_obo()


def get_json_download(prefix: str) -> str | None:
    """Get the download link for the latest OBOGraph JSON file."""
    entry = get_resource(prefix)
    if entry is None:
        return None
    return entry.get_download_obograph()


def get_owl_download(prefix: str) -> str | None:
    """Get the download link for the latest OWL file."""
    entry = get_resource(prefix)
    if entry is None:
        return None
    return entry.get_download_owl()


def get_rdf_download(prefix: str) -> str | None:
    """Get the download link for the RDF file."""
    entry = get_resource(prefix)
    if entry is None:
        return None
    return entry.get_download_rdf()


def get_provides_for(prefix: str) -> str | None:
    """Get the resource that the given prefix provides for, or return none if not a provider.

    :param prefix: The prefix to look up
    :returns: The prefix of the resource that the given prefix provides for, if it's a provider.
        This is the inverse of :func:`get_provided_by`.

    >>> assert get_provides_for("pdb") is None
    >>> assert "pdb" == get_provides_for("validatordb")
    """
    return manager.get_provides_for(prefix)


def get_provided_by(prefix: str) -> list[str] | None:
    """Get the resources that provide for the given prefix, or return none if the prefix can't be looked up.

    :param prefix: The prefix to look up
    :returns: The prefixes of the resources that provide for the given prefix. This
        is the inverse of :func:`get_provides_for`.

    >>> get_provides_for("validatordb")
    'pdb'
    """
    return manager.get_provided_by(prefix)


def get_part_of(prefix: str) -> str | None:
    """Get the parent resource.

    :param prefix: The prefix to look up
    :returns: The prefixes of the parent resource for this prefix, if one is annotated. This
        is the inverse of :func:`get_has_parts`.

    >>> assert "chembl" in get_part_of("chembl.compound")
    """
    return manager.get_part_of(prefix)


def get_has_parts(prefix: str) -> list[str] | None:
    """Get children resources.

    :param prefix: The prefix to look up
    :returns: The prefixes of resource for which this prefix is the parent. This
        is the inverse of :func:`get_has_parts`.

    >>> assert "chembl.compound" in get_has_parts("chembl")
    """
    return manager.get_has_parts(prefix)


def get_license(prefix: str) -> str | None:
    """Get the license for the resource.

    :param prefix: The prefix to look up
    :returns: The license of the resource (normalized) if available
    """
    entry = get_resource(prefix)
    if entry is None:
        return None
    return entry.get_license()


def is_proprietary(prefix: str) -> bool | None:
    """Get if the prefix is proprietary.

    :param prefix: The prefix to look up
    :returns: If the prefix corresponds to a proprietary resource. Assume false if not annotated explicitly

    >>> assert is_proprietary("eurofir")
    >>> assert not is_proprietary("chebi")
    """
    entry = get_resource(prefix)
    if entry is None:
        return None
    if entry.proprietary is None:
        return False
    return entry.proprietary


def is_obo_foundry(prefix: str) -> bool | None:
    """Get if the prefix has an OBO Foundry link.

    :param prefix: The prefix to look up
    :returns: If the prefix corresponds to an OBO Foundry resource

    >>> assert is_obo_foundry("chebi")
    >>> assert not is_proprietary("pdb")
    """
    entry = get_resource(prefix)
    if entry is None:
        return None
    return entry.get_obofoundry_prefix() is not None


def get_version(prefix: str) -> str | None:
    """Get the version."""
    norm_prefix = manager.normalize_prefix(prefix)
    if norm_prefix is None:
        return None
    return get_versions().get(norm_prefix)


@lru_cache(maxsize=1)
def get_versions() -> Mapping[str, str]:
    """Get a map of prefixes to versions."""
    return manager.get_versions()


def get_curie_pattern(prefix: str, *, use_preferred: bool = False) -> str | None:
    """Get the CURIE pattern for this resource.

    :param prefix: The prefix to look up
    :param use_preferred: Should the preferred prefix be used instead
        of the Bioregistry prefix (if it exists)?
    :return: The regular expression pattern to match CURIEs against
    """
    return manager.get_curie_pattern(prefix, use_preferred=use_preferred)


def get_license_conflicts() -> list[tuple[str, str | None, str | None, str | None]]:
    """Get license conflicts."""
    return manager.get_license_conflicts()


def get_obo_health_url(prefix: str) -> str | None:
    """Get the OBO community health badge."""
    return manager.get_obo_health_url(prefix)


def is_novel(prefix: str) -> bool | None:
    """Check if the prefix is novel to the Bioregistry, i.e., it has no external mappings."""
    return manager.is_novel(prefix)


def get_parts_collections() -> Mapping[str, list[str]]:
    """Group resources' prefixes based on their ``part_of`` entries.

    :returns:
        A dictionary with keys that appear as the values of ``Resource.part_of``
        and whose values are lists of prefixes for resources that have the key
        as a value in its ``part_of`` field.

    .. warning::

        Many of the keys in this dictionary are valid Bioregistry prefixes,
        but this is not necessary. For example, ``ctd`` is one key that
        appears that explicitly has no prefix, since it corresponds to a
        resource and not a vocabulary.
    """
    return manager.get_parts_collections()


def get_obo_context_prefix_map(include_synonyms: bool = False) -> Mapping[str, str]:
    """Get the OBO Foundry prefix map.

    :param include_synonyms: Should synonyms of each prefix also be included as additional prefixes, but with
        the same URL prefix?
    :return: A mapping from prefixes to prefix URLs.
    """
    return manager.get_context_artifacts("obo", include_synonyms=include_synonyms)[0]


def read_contributors(direct_only: bool = False) -> Mapping[str, Attributable]:
    """Get a mapping from contributor ORCID identifiers to author objects."""
    return manager.read_contributors(direct_only=direct_only)


def get_converter(**kwargs: Any) -> curies.Converter:
    """Get a converter from this manager."""
    return manager.get_converter(**kwargs)


def add_resource(resource: Resource) -> None:
    """Add a resource."""
    manager.add_resource(resource)


def get_logo(prefix: str) -> str | None:
    """Get the logo for the resource, if it's available."""
    return manager.get_logo(prefix)


def get_mailing_list(prefix: str) -> str | None:
    """Get the mailing list for the resource, if it's available."""
    return manager.get_mailing_list(prefix)
