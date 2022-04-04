# -*- coding: utf-8 -*-

"""Pydantic models for the Bioregistry."""

import json
import logging
import pathlib
import re
import textwrap
from functools import lru_cache
from typing import (
    Any,
    Callable,
    ClassVar,
    Dict,
    List,
    Mapping,
    Optional,
    Sequence,
    Set,
    Union,
)

import pydantic.schema
from pydantic import BaseModel, Field

from bioregistry import constants as brc
from bioregistry.constants import BIOREGISTRY_REMOTE_URL, URI_FORMAT_KEY
from bioregistry.license_standardizer import standardize_license
from bioregistry.schema.utils import EMAIL_RE

try:
    from typing import Literal  # type:ignore
except ImportError:
    from typing_extensions import Literal  # type:ignore

__all__ = [
    "Attributable",
    "Author",
    "Provider",
    "Resource",
    "Collection",
    "Registry",
    "Context",
    "get_json_schema",
]

logger = logging.getLogger(__name__)

HERE = pathlib.Path(__file__).parent.resolve()
SCHEMA_PATH = HERE.joinpath("schema.json")

#: Search string for skipping formatters containing this
IDOT_SKIP = "identifiers.org"


def _dedent(s: str) -> str:
    return textwrap.dedent(s).replace("\n", " ").replace("  ", " ").strip()


ORCID_DESCRIPTION = _dedent(
    """\
The Open Researcher and Contributor Identifier (ORCiD) provides
researchers with an open, unambiguous identifier for connecting
various digital assets (e.g., publications, reviews) across the
semantic web. An account can be made in seconds at https://orcid.org.
"""
)


class Attributable(BaseModel):
    """An upper-level metadata for a researcher."""

    name: str = Field(description="The full name of the researcher")

    orcid: Optional[str] = Field(
        title="Open Researcher and Contributor Identifier",
        description=ORCID_DESCRIPTION,
    )

    email: Optional[str] = Field(
        title="Email address",
        description="The email address specific to the researcher.",
        # regex=EMAIL_RE_STR,
    )

    #: The GitHub handle for the author
    github: Optional[str] = Field(
        title="GitHub handle",
        description=_dedent(
            """\
    The GitHub handle enables contacting the researcher on GitHub:
    the *de facto* version control in the computer sciences and life sciences.
    """
        ),
    )

    def add_triples(self, graph):
        """Add triples to an RDF graph for this author.

        :param graph: An RDF graph
        :type graph: rdflib.Graph
        :rtype: rdflib.term.Node
        :returns: The RDF node representing this author using an ORCiD URI.
        """
        from rdflib import BNode, Literal
        from rdflib.namespace import RDFS

        if not self.orcid:
            node = BNode()
        else:
            from .constants import orcid

            node = orcid.term(self.orcid)
        graph.add((node, RDFS["label"], Literal(self.name)))
        return node


class Author(Attributable):
    """Metadata for an author."""

    #: This field is redefined on top of :class:`Attributable` to make
    #: it required. Otherwise, it has the same semantics.
    orcid: str = Field(
        ..., title="Open Researcher and Contributor Identifier", description=ORCID_DESCRIPTION
    )


class Provider(BaseModel):
    """A provider."""

    code: str = Field(..., description="A locally unique code within the prefix for the provider")
    name: str = Field(..., description="Name of the provider")
    description: str = Field(..., description="Description of the provider")
    homepage: str = Field(..., description="Homepage of the provider")
    uri_format: str = Field(
        ...,
        title="URI Format",
        description="The URI format string, which must have at least one ``$1`` in it",
    )

    def resolve(self, identifier: str) -> str:
        """Resolve the identifier into a URI.

        :param identifier: The identifier in the semantic space
        :return: The URI for the identifier
        """
        return self.uri_format.replace("$1", identifier)


class Resource(BaseModel):
    """Metadata about an ontology, database, or other resource."""

    prefix: str = Field(..., description="The prefix for this resource", exclude=True)
    name: Optional[str] = Field(
        description="The name of the resource",
    )
    description: Optional[str] = Field(
        description="A description of the resource",
    )
    pattern: Optional[str] = Field(
        description="The regular expression pattern for local unique identifiers in the resource",
    )
    uri_format: Optional[str] = Field(
        title="URI format string",
        description="The URI format string, which must have at least one ``$1`` in it",
    )
    providers: Optional[List[Provider]] = Field(
        description="Additional, non-default providers for the resource",
    )
    homepage: Optional[str] = Field(
        description="The URL for the homepage of the resource, preferably using HTTPS",
    )
    repository: Optional[str] = Field(
        description="The URL for the repository of the resource",
    )
    contact: Optional[Attributable] = Field(
        description=(
            "The contact email address for the resource. This must correspond to a specific "
            "person and not be a listserve nor a shared email account."
        )
    )
    example: Optional[str] = Field(
        description="An example local identifier for the resource, explicitly excluding any redundant "
        "usage of the prefix in the identifier. For example, a GO identifier should only "
        "look like ``1234567`` and not like ``GO:1234567``",
    )
    example_extras: Optional[List[str]] = Field(
        description="Extra example identifiers",
    )
    license: Optional[str] = Field(
        description="The license for the resource",
    )
    version: Optional[str] = Field(
        description="The version for the resource",
    )
    part_of: Optional[str] = Field(
        description=(
            "An annotation between this prefix and a super-prefix. For example, "
            "``chembl.compound`` is a part of ``chembl``."
        )
    )
    provides: Optional[str] = Field(
        description=(
            "An annotation between this prefix and a prefix for which it is redundant. "
            "For example, ``ctd.gene`` has been given a prefix by Identifiers.org, but it "
            "actually just reuses identifies from ``ncbigene``, so ``ctd.gene`` provides ``ncbigene``."
        ),
    )
    download_owl: Optional[str] = Field(
        title="OWL Download URL",
        description=_dedent(
            """\
    The URL to download the resource as an ontology encoded in the OWL format.
    More information about this format can be found at https://www.w3.org/TR/owl2-syntax/.
    """
        ),
    )
    download_obo: Optional[str] = Field(
        title="OBO Download URL",
        description=_dedent(
            """\
    The URL to download the resource as an ontology encoded in the OBO format.
    More information about this format can be found at https://owlcollab.github.io/oboformat/doc/obo-syntax.html.
    """
        ),
    )
    download_json: Optional[str] = Field(
        title="OBO Graph JSON Download URL",
        description=_dedent(
            """
    The URL to download the resource as an ontology encoded in the OBO Graph JSON format.
    More information about this format can be found at https://github.com/geneontology/obographs.
    """
        ),
    )
    banana: Optional[str] = Field(
        description=_dedent(
            """\
    The `banana` is a generalization of the concept of the "namespace embedded in local unique identifier".
    Many OBO foundry ontologies use the redundant uppercased name of the ontology in the local identifier,
    such as the Gene Ontology, which makes the prefixes have a redundant usage as in ``GO:GO:1234567``.
    The `banana` tag explicitly annotates the part in the local identifier that should be stripped, if found.
    While the Bioregistry automatically knows how to handle all OBO Foundry ontologies' bananas because the
    OBO Foundry provides the "preferredPrefix" field, the banana can be annotated on non-OBO ontologies to
    more explicitly write the beginning part of the identifier that should be stripped. This allowed for
    solving one of the long-standing issues with the Identifiers.org resolver (e.g., for ``oma.hog``; see
    https://github.com/identifiers-org/identifiers-org.github.io/issues/155) as well as better annotate
    new entries, such as SwissMap Lipids, which have the prefix ``swisslipid`` but have the redundant information
    ``SLM:`` in the beginning of identifiers. Therefore, ``SLM:`` is the banana.
    """
        ),
    )
    deprecated: Optional[bool] = Field(
        description=_dedent(
            """\
    A flag denoting if this resource is deprecated. Currently, this is a blanket term
    that covers cases when the prefix is no longer maintained, when it has been rolled
    into another resource, when the website related to the resource goes down, or any
    other reason that it's difficult or impossible to find full metadata on the resource.
    If this is set to true, please add a comment explaining why. This flag will override
    annotations from the OLS, OBO Foundry, and Prefix Commons on the deprecation status,
    since they often disagree and are very conservative in calling dead resources.
    """
        ),
    )
    mappings: Optional[Dict[str, str]] = Field(
        description=_dedent(
            """\
    A dictionary of metaprefixes (i.e., prefixes for registries) to prefixes in external registries.
    These also correspond to the registry-specific JSON fields in this model like ``miriam`` field.
    """
        ),
    )
    synonyms: Optional[List[str]] = Field(
        description=_dedent(
            """\
    A list of synonyms for the prefix of this resource. These are used in normalization of
    prefixes and are a useful reference tool for prefixes that are written many ways. For
    example, ``snomedct`` has many synonyms including typos like ``SNOWMEDCT``, lexical
    variants like ``SNOMED_CT``, version-variants like ``SNOMEDCT_2010_1_31``, and tons
    of other nonsense like ``SNOMEDCTCT``.
    """
        ),
    )
    references: Optional[List[str]] = Field(
        description="A list of URLs to also see, such as publications describing the resource",
    )
    appears_in: Optional[List[str]] = Field(
        description="A list of prefixes that use this resource for xrefs, provenance, etc.",
    )
    depends_on: Optional[List[str]] = Field(
        description="A list of prefixes that use this resource depends on, e.g., ontologies that import each other.",
    )

    namespace_in_lui: Optional[bool] = Field(
        title="Namespace Embedded in Local Unique Identifier",
        description=_dedent(
            """\
    A flag denoting if the namespace is embedded in the LUI (if this is true and it is not accompanied by a banana,
    assume that the banana is the prefix in all caps plus a colon, as is standard in OBO). Currently this flag
    is only used to override identifiers.org in the case of ``gramene.growthstage``, ``oma.hog``, and ``vario``.
    """
        ),
    )
    no_own_terms: Optional[bool] = Field(
        description=_dedent(
            """\
    A flag denoting if the resource mints its own identifiers. Omission or explicit marking as false means
    that the resource does have its own terms. This is most applicable to ontologies, specifically application
    ontologies, which only reuse terms from others. One example is ChIRO.
    """
        ),
    )
    #: A field for a free text comment.
    comment: Optional[str] = Field(
        description="A field for a free text comment",
    )

    contributor: Optional[Author] = Field(
        description=_dedent(
            """\
    The contributor of the prefix to the Bioregistry, including at a minimum their name and ORCiD and
    optionall their email address and GitHub handle. All entries curated through the Bioregistry GitHub
    Workflow must contain this field.
    """
        ),
    )
    contributor_extras: Optional[List[Author]] = Field(
        description="Additional contributors besides the original submitter.",
    )

    reviewer: Optional[Author] = Field(
        description=_dedent(
            """\
    The reviewer of the prefix to the Bioregistry, including at a minimum their name and ORCiD and
    optionall their email address and GitHub handle. All entries curated through the Bioregistry GitHub
    Workflow should contain this field pointing to the person who reviewed it on GitHub.
    """
        )
    )
    proprietary: Optional[bool] = Field(
        description=_dedent(
            """\
    A flag to denote if this database is proprietary and therefore can not be included in normal quality control
    checks nor can it be resolved. Omission or explicit marking as false means that the resource is not proprietary.
    """
        ),
    )
    #: An annotation between this prefix and another prefix if they share the same provider IRI to denote that the
    #: other prefix should be considered as the canonical prefix to which IRIs should be contracted as CURIEs.
    #:
    #: .. seealso::
    #:
    #:    This field was added and described in detail in https://github.com/biopragmatics/bioregistry/pull/164
    has_canonical: Optional[str] = Field(
        description="If this shares an IRI with another entry, maps to which should be be considered as canonical",
    )
    preferred_prefix: Optional[str] = Field(
        description=_dedent(
            """\
    An annotation of stylization of the prefix. This appears in OBO ontologies like
    FBbt as well as databases like NCBIGene. If it's not given, then assume that
    the normalized prefix used in the Bioregistry is canonical.
    """
        ),
    )
    #: External data from Identifiers.org's MIRIAM Database
    miriam: Optional[Mapping[str, Any]]
    #: External data from the Name-to-Thing service
    n2t: Optional[Mapping[str, Any]]
    #: External data from Prefix Commons
    prefixcommons: Optional[Mapping[str, Any]]
    #: External data from Wikidata Properties
    wikidata: Optional[Mapping[str, Any]]
    #: External data from the Gene Ontology's custom registry
    go: Optional[Mapping[str, Any]]
    #: External data from the Open Biomedical Ontologies (OBO) Foundry catalog
    obofoundry: Optional[Mapping[str, Any]]
    #: External data from the BioPortal ontology repository
    bioportal: Optional[Mapping[str, Any]]
    #: External data from the Ontology Lookup Service
    ols: Optional[Mapping[str, Any]]
    #: External data from the NCBI Genbank's custom registry
    ncbi: Optional[Mapping[str, Any]]
    #: External data from UniProt's custom registry
    uniprot: Optional[Mapping[str, Any]]
    #: External data from the BioLink Model's custom registry
    biolink: Optional[Mapping[str, Any]]
    #: External data from the Cellosaurus custom registry
    cellosaurus: Optional[Mapping[str, Any]]
    #: External data from the OntoBee
    ontobee: Optional[Mapping[str, Any]]
    #: External data from ChemInf
    cheminf: Optional[Mapping[str, Any]]
    #: External data from FAIRsharing
    fairsharing: Optional[Mapping[str, Any]]

    def get_external(self, metaprefix) -> Mapping[str, Any]:
        """Get an external registry."""
        return self.dict().get(metaprefix) or dict()

    def get_mapped_prefix(self, metaprefix: str) -> Optional[str]:
        """Get the prefix for the given external.

        :param metaprefix: The metaprefix for the external resource
        :returns: The prefix in the external registry, if it could be mapped

        >>> from bioregistry import get_resource
        >>> get_resource("chebi").get_mapped_prefix("wikidata")
        'P683'
        """
        # TODO is this even a good idea? is this effectively the same as get_external?
        return (self.get_mappings() or {}).get(metaprefix)

    def get_prefix_key(self, key: str, metaprefixes: Union[str, Sequence[str]]):
        """Get a key enriched by the given external resources' data."""
        rv = self.dict().get(key)
        if rv is not None:
            return rv
        if isinstance(metaprefixes, str):
            metaprefixes = [metaprefixes]
        for metaprefix in metaprefixes:
            external = self.get_external(metaprefix)
            if external is None:
                raise TypeError
            rv = external.get(key)
            if rv is not None:
                return rv
        return None

    def get_default_uri(self, identifier: str) -> Optional[str]:
        """Return the default URI for the identifier.

        :param identifier: The local identifier in the nomenclature represented by this resource
        :returns: The first-party provider URI for the local identifier, if one can be constructed

        >>> from bioregistry import get_resource
        >>> get_resource("chebi").get_default_uri("24867")
        'https://www.ebi.ac.uk/chebi/searchId.do?chebiId=CHEBI:24867'
        """
        fmt = self.get_default_format()
        if fmt is None:
            return None
        return fmt.replace("$1", identifier)

    def __setitem__(self, key, value):  # noqa: D105
        setattr(self, key, value)

    def get_banana(self) -> Optional[str]:
        """Get the optional redundant prefix to go before an identifier.

        A "banana" is an embedded prefix that isn't actually part of the identifier.
        Usually this corresponds to the prefix itself, with some specific stylization
        such as in the case of FBbt. The banana does NOT include a colon ":" at the end

        :return: The banana, if the prefix is valid and has an associated banana.

        Explicitly annotated banana

        >>> from bioregistry import get_resource
        >>> get_resource("go.ref").get_banana()
        'GO_REF'

        Banana imported through OBO Foundry

        >>> get_resource("fbbt").get_banana()
        'FBbt'

        Banana inferred for OBO Foundry ontology

        >>> get_resource("chebi").get_banana()
        'CHEBI'

        No banana, no namespace in LUI

        >>> get_resource("pdb").get_banana()
        None

        Banana is not inferred for OBO Foundry ontologies
        that were imported:
        >>> get_resource("ncit").get_banana()
        None
        >>> get_resource("ncbitaxon").get_banana()
        None
        """
        if self.banana is not None:
            return self.banana
        if self.namespace_in_lui is False:
            return None  # override for a few situations
        obo_preferred_prefix = self.get_obo_preferred_prefix()
        if obo_preferred_prefix is not None:
            return obo_preferred_prefix
        # TODO consider reinstating all preferred prefixes should
        #  be considered as secondary bananas
        return None

    def get_default_format(self) -> Optional[str]:
        """Get the default, first-party URI prefix.

        :returns: The first-party URI prefix string, if available.

        >>> from bioregistry import get_resource
        >>> get_resource("ncbitaxon").get_default_format()
        'https://www.ncbi.nlm.nih.gov/Taxonomy/Browser/wwwtax.cgi?mode=Info&id=$1'
        >>> get_resource("go").get_default_format()
        'http://amigo.geneontology.org/amigo/term/GO:$1'
        """
        if self.uri_format is not None:
            return self.uri_format
        for metaprefix, key in [
            ("miriam", URI_FORMAT_KEY),
            ("n2t", URI_FORMAT_KEY),
            ("go", URI_FORMAT_KEY),
            ("prefixcommons", URI_FORMAT_KEY),
            ("wikidata", URI_FORMAT_KEY),
            ("uniprot", URI_FORMAT_KEY),
            ("cellosaurus", URI_FORMAT_KEY),
        ]:
            rv = self.get_external(metaprefix).get(key)
            if rv is not None and _allowed_uri_format(rv):
                return rv
        return None

    def get_synonyms(self) -> Set[str]:
        """Get synonyms."""
        # TODO aggregate even more from xrefs
        return set(self.synonyms or {})

    def get_preferred_prefix(self) -> Optional[str]:
        """Get the preferred prefix (e.g., with stylization) if it exists.

        :returns: The preferred prefix, if annotated in the Bioregistry or OBO Foundry.

        No preferred prefix annotation, defaults to normalized prefix
        >>> from bioregistry import get_resource
        >>> get_resource("rhea").get_preferred_prefix()
        None

        Preferred prefix defined in the Bioregistry
        >>> get_resource("wb").get_preferred_prefix()
        'WormBase'

        Preferred prefix defined in the OBO Foundry
        >>> get_resource("fbbt").get_preferred_prefix()
        'FBbt'

        Preferred prefix from the OBO Foundry overridden by the Bioregistry
        (see also https://github.com/OBOFoundry/OBOFoundry.github.io/issues/1559)
        >>> get_resource("dpo").get_preferred_prefix()
        'DPO'
        """
        if self.preferred_prefix is not None:
            return self.preferred_prefix
        obo_preferred_prefix = self.get_obo_preferred_prefix()
        if obo_preferred_prefix is not None:
            return obo_preferred_prefix
        return None

    def get_obo_preferred_prefix(self) -> Optional[str]:
        """Get the OBO preferred prefix, if this resource is mapped to the OBO Foundry."""
        if self.obofoundry is None:
            return None
        # if explicitly annotated, use it. Otherwise, the capitalized version
        # of the OBO Foundry ID is the preferred prefix (e.g., for GO)
        return self.obofoundry.get("preferredPrefix", self.obofoundry["prefix"].upper())

    def get_mappings(self) -> Optional[Mapping[str, str]]:
        """Get the mappings to external registries, if available."""
        from ..utils import read_metaregistry

        rv: Dict[str, str] = {}
        rv.update(self.mappings or {})  # This will be the replacement later
        for metaprefix in read_metaregistry():
            external = self.get_external(metaprefix)
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

    def get_name(self) -> Optional[str]:
        """Get the name for the given prefix, it it's available."""
        return self.get_prefix_key(
            "name",
            ("obofoundry", "ols", "wikidata", "go", "ncbi", "bioportal", "miriam", "cellosaurus"),
        )

    def get_description(self, use_markdown: bool = False) -> Optional[str]:
        """Get the description for the given prefix, if available."""
        if self.description and use_markdown:
            import markupsafe
            from markdown import markdown

            return markupsafe.Markup(markdown(self.description))
        rv = self.get_prefix_key(
            "description", ("miriam", "ols", "obofoundry", "wikidata", "fairsharing")
        )
        if rv is not None:
            return rv
        if self.cellosaurus and "category" in self.cellosaurus:
            return self.cellosaurus["category"]
        return None

    def get_pattern(self) -> Optional[str]:
        """Get the pattern for the given prefix, if it's available.

        :returns: The pattern for the prefix, if it is available, using the following order of preference:
            1. Custom
            2. MIRIAM
            3. Wikidata
        """
        if self.pattern is not None:
            return self.pattern
        rv = self.get_prefix_key("pattern", ("miriam", "wikidata"))
        if rv is None:
            return None
        return _clean_pattern(rv)

    def get_pattern_re(self):
        """Get the compiled pattern for the given prefix, if it's available."""
        pattern = self.get_pattern()
        if pattern is None:
            return None
        return re.compile(pattern)

    def get_namespace_in_lui(self) -> Optional[bool]:
        """Check if the namespace should appear in the LUI."""
        if self.namespace_in_lui is not None:
            return self.namespace_in_lui
        return self.get_prefix_key("namespaceEmbeddedInLui", "miriam")

    def get_homepage(self) -> Optional[str]:
        """Return the homepage, if available."""
        return self.get_prefix_key(
            "homepage",
            ("obofoundry", "ols", "miriam", "n2t", "wikidata", "go", "ncbi", "cellosaurus"),
        )

    def get_repository(self) -> Optional[str]:
        """Return the repository, if available."""
        if self.repository:
            return self.repository
        return self.get_prefix_key("repository", "obofoundry")

    def get_contact(self) -> Optional[Attributable]:
        """Get the contact, if available."""
        name = self.get_contact_name()
        if name is None:
            return None
        return Attributable(
            name=name,
            email=self.get_contact_email(),
            orcid=self.get_contact_orcid(),
            github=self.get_contact_github(),
        )

    def get_contact_email(self) -> Optional[str]:
        """Return the contact email, if available.

        :returns: The resource's contact email address, if it is available.

        >>> from bioregistry import get_resource
        >>> get_resource("bioregistry").get_contact_email()  # from bioregistry curation
        'cthoyt@gmail.com'
        >>> get_resource("chebi").get_contact_email()
        'amalik@ebi.ac.uk'
        """
        if self.contact and self.contact.email:
            return self.contact.email
        # FIXME if contact is not none but email is, this will have a problem after
        rv = self.get_prefix_key("contact", ("obofoundry", "ols"))
        if rv and not EMAIL_RE.match(rv):
            logger.warning("[%s] invalid email address listed: %s", self.name, rv)
            return None
        return rv

    def get_contact_name(self) -> Optional[str]:
        """Return the contact name, if available.

        :returns: The resource's contact name, if it is available.

        >>> from bioregistry import get_resource
        >>> get_resource("bioregistry").get_contact_name()  # from bioregistry curation
        'Charles Tapley Hoyt'
        >>> get_resource("chebi").get_contact_name()
        'Adnan Malik'
        """
        if self.contact and self.contact.name:
            return self.contact.name
        if self.obofoundry and "contact.label" in self.obofoundry:
            return self.obofoundry["contact.label"]
        return None

    def get_contact_github(self) -> Optional[str]:
        """Return the contact GitHub handle, if available.

        :returns: The resource's contact GitHub handle, if it is available.

        >>> from bioregistry import get_resource
        >>> get_resource("bioregistry").get_contact_github()  # from bioregistry curation
        'cthoyt'
        >>> get_resource("agro").get_contact_github()  # from OBO Foundry
        'marieALaporte'
        """
        if self.contact and self.contact.github:
            return self.contact.github
        if self.obofoundry and "contact.github" in self.obofoundry:
            return self.obofoundry["contact.github"]
        return None

    def get_contact_orcid(self) -> Optional[str]:
        """Return the contact ORCiD, if available.

        :returns: The resource's contact ORCiD, if it is available.

        >>> from bioregistry import get_resource
        >>> get_resource("bioregistry").get_contact_orcid()  # from bioregistry curation
        '0000-0003-4423-4370'
        >>> get_resource("aero").get_contact_orcid()
        '0000-0002-9551-6370'
        """
        if self.contact and self.contact.orcid:
            return self.contact.orcid
        if self.obofoundry and "contact.orcid" in self.obofoundry:
            return self.obofoundry["contact.orcid"]
        return None

    def get_example(self) -> Optional[str]:
        """Get an example identifier, if it's available."""
        example = self.example
        if example is not None:
            return example
        miriam_example = self.get_external("miriam").get("sampleId")
        if miriam_example is not None:
            return miriam_example
        example = self.get_external("ncbi").get("example")
        if example is not None:
            return example
        return None

    def is_deprecated(self) -> bool:
        """Return if the given prefix corresponds to a deprecated resource.

        :returns: If the prefix has been explicitly marked as deprecated either by
            the Bioregistry, OBO Foundry, OLS, or MIRIAM. If no marks are present,
            assumed not to be deprecated.

        >>> from bioregistry import get_resource
        >>> assert get_resource("imr").is_deprecated()  # marked by OBO
        >>> assert get_resource("iro").is_deprecated() # marked by Bioregistry
        >>> assert get_resource("miriam.collection").is_deprecated() # marked by MIRIAM
        """
        if self.deprecated is not None:
            return self.deprecated
        for key in ("obofoundry", "ols", "miriam"):
            external = self.get_external(key)
            if external.get("deprecated"):
                return True
        return False

    def get_obofoundry_prefix(self) -> Optional[str]:
        """Get the OBO Foundry prefix if available.

        :returns: The OBO prefix, if available.

        >>> from bioregistry import get_resource
        >>> get_resource("go").get_obofoundry_prefix()  # standard
        'GO'
        >>> get_resource("ncbitaxon").get_obofoundry_prefix()  # mixed case
        'NCBITaxon'
        >>> assert get_resource("sty").get_obofoundry_prefix() is None
        """
        return self.get_mapped_prefix("obofoundry")

    def get_obofoundry_uri_prefix(self) -> Optional[str]:
        """Get the OBO Foundry URI prefix for this entry, if possible.

        :returns: The OBO PURL URI prefix corresponding to the prefix, if mappable.

        >>> from bioregistry import get_resource
        >>> get_resource("go").get_obofoundry_uri_prefix()  # standard
        'http://purl.obolibrary.org/obo/GO_'
        >>> get_resource("ncbitaxon").get_obofoundry_uri_prefix()  # mixed case
        'http://purl.obolibrary.org/obo/NCBITaxon_'
        >>> assert get_resource("sty").get_obofoundry_uri_prefix() is None
        """
        obo_prefix = self.get_obofoundry_prefix()
        if obo_prefix is None:
            return None
        return f"http://purl.obolibrary.org/obo/{obo_prefix}_"

    def get_obofoundry_uri_format(self) -> Optional[str]:
        """Get the OBO Foundry URI format string for this entry, if possible.

        :returns: The OBO PURL format string, if available.

        >>> from bioregistry import get_resource
        >>> get_resource("go").get_obofoundry_uri_format()  # standard
        'http://purl.obolibrary.org/obo/GO_$1'
        >>> get_resource("ncbitaxon").get_obofoundry_uri_format()  # mixed case
        'http://purl.obolibrary.org/obo/NCBITaxon_$1'
        >>> assert get_resource("sty").get_obofoundry_uri_format() is None
        """
        rv = self.get_obofoundry_uri_prefix()
        if rv is None:
            return None
        return f"{rv}$1"

    def get_prefixcommons_uri_format(self) -> Optional[str]:
        """Get the Prefix Commons URI format string for this entry, if available.

        :returns: The Prefix Commons URI format string, if available.

        >>> from bioregistry import get_resource
        >>> get_resource("hgmd").get_prefixcommons_uri_format()
        'http://www.hgmd.cf.ac.uk/ac/gene.php?gene=$1'
        """
        return self.get_external("prefixcommons").get(URI_FORMAT_KEY)

    def get_identifiers_org_prefix(self) -> Optional[str]:
        """Get the identifiers.org prefix if available.

        :returns: The Identifiers.org/MIRIAM prefix corresponding to the prefix, if mappable.

        >>> from bioregistry import get_resource
        >>> get_resource('chebi').get_identifiers_org_prefix()
        'chebi'
        >>> get_resource('ncbitaxon').get_identifiers_org_prefix()
        'taxonomy'
        >>> assert get_resource('MONDO').get_identifiers_org_prefix() is None
        """
        return self.get_mapped_prefix("miriam")

    def get_miriam_uri_prefix(self) -> Optional[str]:
        """Get the Identifiers.org URI prefix for this entry, if possible.

        :returns: The Identifiers.org/MIRIAM URI prefix, if available.

        >>> from bioregistry import get_resource
        >>> get_resource('ncbitaxon').get_miriam_uri_prefix()
        'https://identifiers.org/taxonomy:'
        >>> get_resource('go').get_miriam_uri_prefix()
        'https://identifiers.org/GO:'
        >>> assert get_resource('sty').get_miriam_uri_prefix() is None
        """
        miriam_prefix = self.get_identifiers_org_prefix()
        if miriam_prefix is None:
            return None
        if self.get_namespace_in_lui():
            # not exact solution, some less common ones don't use capitalization
            # align with the banana solution
            miriam_prefix = miriam_prefix.upper()
        return f"https://identifiers.org/{miriam_prefix}:"

    def get_miriam_uri_format(self) -> Optional[str]:
        """Get the Identifiers.org URI format string for this entry, if possible.

        :returns: The Identifiers.org/MIRIAM URL format string, if available.

        >>> from bioregistry import get_resource
        >>> get_resource('ncbitaxon').get_miriam_uri_format()
        'https://identifiers.org/taxonomy:$1'
        >>> get_resource('go').get_miriam_uri_format()
        'https://identifiers.org/GO:$1'
        >>> assert get_resource('sty').get_miriam_uri_format() is None
        """
        miriam_url_prefix = self.get_miriam_uri_prefix()
        if miriam_url_prefix is None:
            return None
        return f"{miriam_url_prefix}$1"

    def get_nt2_uri_prefix(self) -> Optional[str]:
        """Get the Name-to-Thing URI prefix for this entry, if possible."""
        n2t_prefix = self.get_mapped_prefix("n2t")
        if n2t_prefix is None:
            return None
        return f"https://n2t.net/{n2t_prefix}:"

    def get_n2t_uri_format(self):
        """Get the Name-to-Thing URI format string, if available."""
        n2t_uri_prefix = self.get_nt2_uri_prefix()
        if n2t_uri_prefix is None:
            return None
        return f"{n2t_uri_prefix}$1"

    def get_scholia_prefix(self):
        """Get the Scholia prefix, if available."""
        return self.get_mapped_prefix("scholia")

    def get_ols_prefix(self) -> Optional[str]:
        """Get the OLS prefix if available."""
        return self.get_mapped_prefix("ols")

    def get_ols_uri_prefix(self) -> Optional[str]:
        """Get the OLS URI prefix for this entry, if possible.

        :returns: The OLS URI prefix, if available.

        .. warning:: This doesn't have a normal form, so it only works for OBO Foundry at the moment.

        >>> from bioregistry import get_resource
        >>> get_resource("go").get_ols_uri_prefix()  # standard
        'https://www.ebi.ac.uk/ols/ontologies/go/terms?iri=http://purl.obolibrary.org/obo/GO_'
        >>> get_resource("ncbitaxon").get_ols_uri_prefix()  # mixed case
        'https://www.ebi.ac.uk/ols/ontologies/ncbitaxon/terms?iri=http://purl.obolibrary.org/obo/NCBITaxon_'
        >>> assert get_resource("sty").get_ols_uri_prefix() is None
        """
        ols_prefix = self.get_ols_prefix()
        if ols_prefix is None:
            return None
        obo_format = self.get_obofoundry_uri_prefix()
        if obo_format:
            return f"https://www.ebi.ac.uk/ols/ontologies/{ols_prefix}/terms?iri={obo_format}"
        # TODO find examples, like for EFO on when it's not based on OBO Foundry PURLs
        return None

    def get_ols_uri_format(self) -> Optional[str]:
        """Get the OLS URI format string for this entry, if possible.

        :returns: The OLS format string, if available.

        .. warning:: This doesn't have a normal form, so it only works for OBO Foundry at the moment.

        >>> from bioregistry import get_resource
        >>> get_resource("go").get_ols_uri_format()  # standard
        'https://www.ebi.ac.uk/ols/ontologies/go/terms?iri=http://purl.obolibrary.org/obo/GO_$1'
        >>> get_resource("ncbitaxon").get_ols_uri_format()  # mixed case
        'https://www.ebi.ac.uk/ols/ontologies/ncbitaxon/terms?iri=http://purl.obolibrary.org/obo/NCBITaxon_$1'
        >>> assert get_resource("sty").get_ols_uri_format() is None
        """
        ols_url_prefix = self.get_ols_uri_prefix()
        if ols_url_prefix is None:
            return None
        return f"{ols_url_prefix}$1"

    URI_FORMATTERS: ClassVar[Mapping[str, Callable[["Resource"], Optional[str]]]] = {
        "default": get_default_format,
        "obofoundry": get_obofoundry_uri_format,
        "prefixcommons": get_prefixcommons_uri_format,
        "miriam": get_miriam_uri_format,
        "n2t": get_n2t_uri_format,
        "ols": get_ols_uri_format,
        # "bioportal": lambda x: ...,
    }

    DEFAULT_URI_FORMATTER_PRIORITY: ClassVar[Sequence[str]] = (
        "default",
        "obofoundry",
        "prefixcommons",
        "miriam",
        "n2t",
        "ols",
        # "bioportal",
    )

    def get_uri_format(self, priority: Optional[Sequence[str]] = None) -> Optional[str]:
        """Get the URI format string for the given prefix, if it's available.

        :param priority: The priority order of metaresources to use for format URI lookup.
            The default is:

            1. Default first party (from bioregistry, prefix commons, or miriam)
            2. OBO Foundry
            3. Prefix Commons
            4. Identifiers.org
            5. N2T
            6. OLS
            7. BioPortal

        :return: The best URI format string, where the ``$1`` should be replaced by a
            local unique identifier. ``$1`` could potentially appear multiple times.

        >>> from bioregistry import get_resource
        >>> get_resource("chebi").get_uri_format()
        'https://www.ebi.ac.uk/chebi/searchId.do?chebiId=CHEBI:$1'

        If you want to specify a different priority order, you can do so with the ``priority`` keyword. This
        is of particular interest to ontologists and semantic web people who might want to use ``purl.obolibrary.org``
        URL prefixes over the URL prefixes corresponding to the first-party providers for each resource (e.g., the
        ChEBI example above). Do so like:

        >>> from bioregistry import get_resource
        >>> priority = ['obofoundry', 'bioregistry', 'prefixcommons', 'miriam', 'ols']
        >>> get_resource("chebi").get_uri_format(priority=priority)
        'http://purl.obolibrary.org/obo/CHEBI_$1'
        """
        # TODO add examples in doctests for prefix commons, identifiers.org, and OLS
        for metaprefix in priority or self.DEFAULT_URI_FORMATTER_PRIORITY:
            formatter = self.URI_FORMATTERS.get(metaprefix)
            if formatter is None:
                logger.warning("count not get formatter for %s", metaprefix)
                continue
            rv = formatter(self)
            if rv is not None:
                return rv
        return None

    def get_uri_prefix(self, priority: Optional[Sequence[str]] = None) -> Optional[str]:
        """Get a well-formed URI prefix, if available.

        :param priority: The prioirty order for :func:`get_format`.
        :return: The URI prefix. Similar to what's returned by :func:`get_uri_format`, but
            it MUST have only one ``$1`` and end with ``$1`` to use thie function.

        >>> import bioregistry
        >>> bioregistry.get_uri_prefix('chebi')
        'https://www.ebi.ac.uk/chebi/searchId.do?chebiId=CHEBI:'
        """
        # TODO shorten this with similar logic to get_uri_format
        fmt = self.get_uri_format(priority=priority)
        if fmt is None:
            logging.debug("term missing formatter: %s", self.name)
            return None
        count = fmt.count("$1")
        if 0 == count:
            logging.debug("formatter missing $1: %s", self.name)
            return None
        if fmt.count("$1") != 1:
            logging.debug("formatter has multiple $1: %s", self.name)
            return None
        if not fmt.endswith("$1"):
            logging.debug("formatter does not end with $1: %s", self.name)
            return None
        return fmt[: -len("$1")]

    def get_extra_providers(self) -> List[Provider]:
        """Get a list of all extra providers."""
        rv = []
        if self.providers is not None:
            rv.extend(self.providers)
        if self.miriam:
            for p in self.miriam.get("providers", []):
                rv.append(Provider(**p))
        return rv

    def standardize_identifier(self, identifier: str, prefix: Optional[str] = None) -> str:
        """Normalize the identifier to not have a redundant prefix or banana.

        :param identifier: The identifier in the CURIE
        :param prefix: If an optional prefix is passed, checks that this isn't also used as a caseolded banana
            like in ``go:go:1234567``, which shouldn't techinncally be right becauase the banana for gene ontology
            is ``GO``.
        :return: A normalized identifier, possibly with banana/redundant prefix removed

        Examples with explicitly annotated bananas:
        >>> from bioregistry import get_resource
        >>> get_resource("vario").standardize_identifier('0376')
        '0376'
        >>> get_resource("vario").standardize_identifier('VariO:0376')
        '0376'
        >>> get_resource("swisslipid").standardize_identifier('000000001')
        '000000001'
        >>> get_resource("swisslipid").standardize_identifier('SLM:000000001')
        '000000001'

        Examples with bananas from OBO:
        >>> get_resource("fbbt").standardize_identifier('00007294')
        '00007294'
        >>> get_resource("fbbt").standardize_identifier('FBbt:00007294')
        '00007294'
        >>> get_resource("chebi").standardize_identifier('1234')
        '1234'
        >>> get_resource("chebi").standardize_identifier('CHEBI:1234')
        '1234'

        Examples from OBO Foundry that should not have a redundant
        prefix added:
        >>> get_resource("ncit").standardize_identifier("C73192")
        'C73192'
        >>> get_resource("ncbitaxon").standardize_identifier("9606")
        '9606'

        Standard:
        >>> get_resource("pdb").standardize_identifier('00000020')
        '00000020'
        """
        banana = self.get_banana()
        if banana and identifier.startswith(f"{banana}:"):
            return identifier[len(banana) + 1 :]
        elif prefix is not None and identifier.casefold().startswith(f"{prefix.casefold()}:"):
            return identifier[len(prefix) + 1 :]
        return identifier

    def miriam_standardize_identifier(self, identifier: str) -> str:
        """Normalize the identifier for legacy usage with MIRIAM using the appropriate banana.

        :param identifier: The identifier in the CURIE
        :return: A normalize identifier, possibly with banana/redundant prefix added

        Because identifiers.org used to have URIs in the form of https://identifiers.org/<prefix>/<prefix>:<identifier>
        for entries annotated with ``namespaceEmbeddedInLui`` as ``true``

        Examples with explicitly annotated bananas:
        >>> from bioregistry import get_resource
        >>> get_resource("vario").miriam_standardize_identifier('0376')
        'VariO:0376'
        >>> get_resource("vario").miriam_standardize_identifier('VariO:0376')
        'VariO:0376'

        Examples with bananas from OBO:
        >>> get_resource("fbbt").miriam_standardize_identifier('00007294')
        'FBbt:00007294'
        >>> get_resource("fbbt").miriam_standardize_identifier('FBbt:00007294')
        'FBbt:00007294'

        Examples from OBO Foundry:
        >>> get_resource("chebi").miriam_standardize_identifier('1234')
        'CHEBI:1234'
        >>> get_resource("chebi").miriam_standardize_identifier('CHEBI:1234')
        'CHEBI:1234'

        Examples from OBO Foundry that should not have a redundant
        prefix added:
        >>> get_resource("ncit").miriam_standardize_identifier("C73192")
        'C73192'
        >>> get_resource("ncbitaxon").miriam_standardize_identifier("9606")
        '9606'

        Standard:
        >>> get_resource("pdb").miriam_standardize_identifier('00000020')
        '00000020'
        """
        # A "banana" is an embedded prefix that isn't actually part of the identifier.
        # Usually this corresponds to the prefix itself, with some specific stylization
        # such as in the case of FBbt. The banana does NOT include a colon ":" at the end
        banana = self.get_banana()
        if banana:
            banana = f"{banana}:"
            if not identifier.startswith(banana):
                return f"{banana}{identifier}"
        # TODO Unnecessary redundant prefix?
        # elif identifier.lower().startswith(f'{prefix}:'):
        #
        return identifier

    def is_canonical_identifier(self, identifier: str) -> Optional[bool]:
        """Check that a local unique identifier is canonical, meaning no bananas."""
        pattern = self.get_pattern_re()
        if pattern is None:
            return None
        return pattern.fullmatch(identifier) is not None

    def is_known_identifier(self, identifier: str) -> Optional[bool]:
        """Check that a local unique identifier can be normalized and also matches a prefix's pattern."""
        return self.is_canonical_identifier(self.standardize_identifier(identifier))

    def get_download_obo(self) -> Optional[str]:
        """Get the download link for the latest OBO file."""
        if self.download_obo:
            return self.download_obo
        return self.get_external("obofoundry").get("download.obo")

    def get_download_obograph(self) -> Optional[str]:
        """Get the download link for the latest OBOGraph JSON file."""
        if self.download_json:
            return self.download_json
        return self.get_external("obofoundry").get("download.json")

    def get_download_owl(self) -> Optional[str]:
        """Get the download link for the latest OWL file."""
        if self.download_owl:
            return self.download_owl
        return (
            self.get_external("obofoundry").get("download.owl")
            or self.get_external("ols").get("version.iri")
            or self.get_external("ols").get("download")
        )

    def get_license(self) -> Optional[str]:
        """Get the license for the resource."""
        if self.license:
            return self.license
        for metaprefix in ("obofoundry", "ols"):
            license_value = standardize_license(self.get_external(metaprefix).get("license"))
            if license_value is not None:
                return license_value
        return None

    def get_version(self) -> Optional[str]:
        """Get the version for the resource."""
        if self.version:
            return self.version
        return self.get_external("ols").get("version")


SchemaStatus = Literal[
    "required", "required*", "present", "present*", "missing", "irrelevant", "irrelevant*"
]
schema_status_map = {
    True: "🟢",
    False: "🔴",
    "required": "🟢",
    "required*": "🟢*",
    "present": "🟡",
    "present*": "🟡*",
    "missing": "🔴",
    "irrelevant": "⚪",
    "irrelevant*": "⚪*",
}
schema_score_map = {
    "required": 3,
    "required*": 3,
    "present": 1,
    "present*": 2,
    "missing": -1,
    "irrelevant": 0,
    "irrelevant*": 0,
}


class RegistrySchema(BaseModel):
    """Metadata about a registry's schema."""

    name: SchemaStatus  # type:ignore
    homepage: SchemaStatus  # type:ignore
    description: SchemaStatus  # type:ignore
    example: SchemaStatus  # type:ignore
    pattern: SchemaStatus  # type:ignore
    provider: SchemaStatus  # type:ignore
    alternate_providers: SchemaStatus  # type:ignore
    synonyms: SchemaStatus  # type:ignore
    license: SchemaStatus  # type:ignore
    version: SchemaStatus  # type:ignore
    contact: SchemaStatus  # type:ignore
    search: bool = Field(
        ..., description="Does this resource have a search functionality for prefixes"
    )
    fair: bool = Field(
        ...,
        description="Does this resource provide a structured dump of the data is easily findable,"
        " accessible, and in a structured format in bulk",
    )
    fair_note: Optional[str] = Field(
        description="Explanation for why data isn't FAIR",
    )

    def score(self) -> int:
        """Calculate a score for the metadata availability in the registry."""
        return (self.search + 2 * self.fair) + sum(
            schema_score_map[x]
            for x in [
                self.name,
                self.homepage,
                self.description,
                self.example,
                self.pattern,
                self.provider,
                self.alternate_providers,
                self.synonyms,
                self.license,
                self.version,
                self.contact,
            ]
        )


class Registry(BaseModel):
    """Metadata about a registry."""

    prefix: str = Field(
        ...,
        description=(
            "The metaprefix for the registry itself. For example, the "
            "metaprefix for Identifiers.org is `miriam`."
        ),
    )
    name: str = Field(..., description="The human-readable label for the registry")
    description: str = Field(..., description="A full description of the registry.")
    homepage: str = Field(..., description="The URL for the homepage of the registry.")
    example: str = Field(..., description="An example prefix inside the registry.")
    availability: RegistrySchema = Field(
        ..., description="A structured description of the metadata that the registry collects"
    )
    download: Optional[str] = Field(
        description="A download link for the data contained in the registry"
    )
    provider_uri_format: Optional[str] = Field(
        description="A URL with a $1 for a prefix to resolve in the registry"
    )
    resolver_uri_format: Optional[str] = Field(
        description="A URL with a $1 for a prefix and $2 for an identifier to resolve in the registry"
    )
    resolver_type: Optional[str] = Field(
        description="An optional type annotation for what kind of resolver it is (i.e., redirect or lookup)"
    )
    contact: Attributable = Field(..., description="The contact for the registry.")
    bioregistry_prefix: Optional[str] = Field(
        description="The prefix for this registry in the Bioregistry"
    )
    logo_url: Optional[str] = Field(
        description="The URL for the logo of the resource",
    )
    license: Optional[str] = Field(
        description="The license under which the resource is redistributed",
    )

    def score(self) -> int:
        """Calculate a metadata score/goodness for this registry."""
        return (
            int(self.provider_uri_format is not None)
            + int(self.resolver_uri_format is not None)
            + int(self.download is not None)
            + int(self.contact is not None)
        ) + self.availability.score()

    def get_provider_uri_prefix(self) -> str:
        """Get provider URI prefix.

        :returns: The URI prefix for the provider for prefixes in this registry.

        >>> from bioregistry import get_registry
        >>> get_registry("fairsharing").get_provider_uri_prefix()
        'https://fairsharing.org/'
        >>> get_registry("miriam").get_provider_uri_prefix()
        'https://registry.identifiers.org/registry/'
        >>> get_registry("n2t").get_provider_uri_prefix()
        'https://bioregistry.io/metaregistry/n2t/'
        """
        if self.provider_uri_format is None or not self.provider_uri_format.endswith("$1"):
            return f"{BIOREGISTRY_REMOTE_URL}/metaregistry/{self.prefix}/"
        return self.provider_uri_format.replace("$1", "")

    def get_provider_uri_format(self, prefix: str) -> Optional[str]:
        """Get the provider string.

        :param prefix: The prefix used in the metaregistry
        :return: The URL in the registry for the prefix, if it's able to provide one

        >>> from bioregistry import get_registry
        >>> get_registry("fairsharing").get_provider_uri_format("FAIRsharing.62qk8w")
        'https://fairsharing.org/FAIRsharing.62qk8w'
        >>> get_registry("miriam").get_provider_uri_format("go")
        'https://registry.identifiers.org/registry/go'
        >>> get_registry("n2t").get_provider_uri_format("go")
        'https://bioregistry.io/metaregistry/n2t/go'
        """
        return self.get_provider_uri_prefix() + prefix

    def get_resolver_uri_format(self, prefix: str) -> str:
        """Generate a provider URI string based on mapping through this registry's vocabulary.

        :param prefix: The prefix used in the metaregistry
        :return: The URI format string to be used for identifiers in the semantic space
            based on this resolver or the Bioregistry's meta-resolver.

        >>> from bioregistry import get_registry
        >>> get_registry("miriam").get_resolver_uri_format("go")
        'https://identifiers.org/go:$1'
        >>> get_registry("cellosaurus").get_resolver_uri_format("go")
        'https://bioregistry.io/metaregistry/cellosaurus/go:$1'
        >>> get_registry("n2t").get_resolver_uri_format("go")
        'https://n2t.net/go:$1'
        """
        if self.resolver_uri_format is None:
            return f"{BIOREGISTRY_REMOTE_URL}/metaregistry/{self.prefix}/{prefix}:$1"
        return self.resolver_uri_format.replace("$1", prefix).replace("$2", "$1")

    def resolve(self, prefix: str, identifier: str) -> Optional[str]:
        """Resolve the registry-specific prefix and identifier.

        :param prefix: The prefix used in the metaregistry
        :param identifier: The identifier in the semantic space
        :return: The URI format string for the given CURIE.

        >>> from bioregistry import get_registry
        >>> get_registry("miriam").resolve("go", "0032571")
        'https://identifiers.org/go:0032571'
        >>> get_registry("cellosaurus").resolve("go", "0032571")
        'https://bioregistry.io/metaregistry/cellosaurus/go:0032571'
        """
        return self.get_resolver_uri_format(prefix).replace("$1", identifier)

    def add_triples(self, graph):
        """Add triples to an RDF graph for this registry.

        :param graph: An RDF graph
        :type graph: rdflib.Graph
        :rtype: rdflib.term.Node
        :returns: The RDF node representing this registry using a Bioregistry IRI.
        """
        from rdflib import Literal
        from rdflib.namespace import DC, FOAF, RDF, RDFS

        from .constants import (
            bioregistry_class_to_id,
            bioregistry_metaresource,
            bioregistry_schema,
        )

        node = bioregistry_metaresource.term(self.prefix)
        graph.add((node, RDF["type"], bioregistry_class_to_id[self.__class__.__name__]))
        graph.add((node, RDFS["label"], Literal(self.name)))
        graph.add((node, DC.description, Literal(self.description)))
        graph.add((node, FOAF["homepage"], Literal(self.homepage)))
        graph.add((node, bioregistry_schema["0000005"], Literal(self.example)))
        if self.provider_uri_format:
            graph.add((node, bioregistry_schema["0000006"], Literal(self.provider_uri_format)))
        if self.resolver_uri_format:
            graph.add((node, bioregistry_schema["0000007"], Literal(self.resolver_uri_format)))
        graph.add((node, bioregistry_schema["0000019"], self.contact.add_triples(graph)))
        return node

    def get_code_link(self) -> Optional[str]:
        """Get a link to the code on github that downloads this resource."""
        path = brc.HERE.joinpath("external", self.prefix).with_suffix(".py")
        if not path.exists():
            return None
        return f"https://github.com/biopragmatics/bioregistry/blob/main/src/bioregistry/external/{self.prefix}.py"


class Collection(BaseModel):
    """A collection of resources."""

    identifier: str = Field(
        ...,
        description="The collection's identifier",
        regex=r"^\d{7}$",
    )
    name: str = Field(
        ...,
        description="The name of the collection",
    )
    description: str = Field(
        ...,
        description="A description of the collection",
    )
    resources: List[str] = Field(
        ...,
        description="A list of prefixes of resources appearing in the collection",
    )
    authors: List[Author] = Field(
        ...,
        description="A list of authors/contributors to the collection",
    )
    #: JSON-LD context name
    context: Optional[str]

    def add_triples(self, graph):
        """Add triples to an RDF graph for this collection.

        :param graph: An RDF graph
        :type graph: rdflib.Graph
        :rtype: rdflib.term.Node
        :returns: The RDF node representing this collection using a Bioregistry IRI.
        """
        from rdflib import Literal
        from rdflib.namespace import DC, DCTERMS, RDF, RDFS

        from .constants import (
            bioregistry_class_to_id,
            bioregistry_collection,
            bioregistry_resource,
        )

        node = bioregistry_collection.term(self.identifier)
        graph.add((node, RDF["type"], bioregistry_class_to_id[self.__class__.__name__]))
        graph.add((node, RDFS["label"], Literal(self.name)))
        graph.add((node, DC.description, Literal(self.description)))

        for author in self.authors:
            author_node = author.add_triples(graph)
            graph.add((node, DC.creator, author_node))

        for resource in self.resources:
            graph.add((node, DCTERMS.hasPart, bioregistry_resource[resource]))

        return node

    def as_context_jsonld(self) -> Mapping[str, Mapping[str, str]]:
        """Get the JSON-LD context from a given collection."""
        return {
            "@context": self.as_prefix_map(),
        }

    def as_prefix_map(self) -> Mapping[str, str]:
        """Get the prefix map for a given collection."""
        from ..uri_format import get_uri_prefix

        rv = {}
        for prefix in self.resources:
            fmt = get_uri_prefix(prefix)
            if fmt is not None:
                rv[prefix] = fmt
        return rv


class Context(BaseModel):
    """A prescriptive context contains configuration for generating fit-for-purpose
    prefix maps to serve various communities based on the standard Bioregistry
    prefix map, custom prefix remapping rules, custom URI prefix remapping rules,
    custom prefix maps, and other community-specific logic.
    """  # noqa:D400,D205

    name: str = Field(
        description="The name of the context",
    )
    description: str = Field(
        description="A description of the context, can include Markdown",
    )
    maintainers: List[Author] = Field(
        description="A list of maintainers for the context",
    )
    prefix_priority: Optional[List[str]] = Field(
        ...,
        description=_dedent(
            """\
            This ordering of metaprefixes (i.e., prefixes for registries)
            is used to determine the priority of which registry's prefixes are used.
            By default, the canonical Bioregistry prefixes are highest priority.
        """
        ),
    )
    include_synonyms: bool = Field(
        False,
        description="Should synonyms be included in the prefix map?",
    )
    use_preferred: bool = Field(
        False,
        description="Should preferred prefixes (i.e., stylized prefixes) be preferred over canonicalized ones?",
    )
    uri_prefix_priority: Optional[List[str]] = Field(
        ...,
        description=_dedent(
            """\
            This ordering of metaprefixes (i.e., prefixes for registries)
            is used to determine the priority of which registry's URI prefixes are used.
            By default, the canonical Bioregistry URI prefixes are highest priority.
         """
        ),
    )
    prefix_remapping: Optional[Dict[str, str]] = Field(
        ...,
        description="This is a mapping from canonical Bioregistry prefixes to custom prefixes used in this context.",
    )
    custom_prefix_map: Optional[Dict[str, str]] = Field(
        ...,
        description=_dedent(
            """\
            This is a custom prefix map (which contains custom URL/URI expansions) that is added after all other
            logic is applied. Keys must either be canonical Bioregistry prefixes, prefixes used based on the
            given prefix priority, or values in the given prefix remapping.
        """
        ),
    )


def _clean_pattern(rv: str) -> str:
    """Clean a regular expression string."""
    rv = rv.rstrip("?")
    if not rv.startswith("^"):
        rv = f"^{rv}"
    if not rv.endswith("$"):
        rv = f"{rv}$"
    return rv


def _allowed_uri_format(rv: str) -> bool:
    """Check that a URI format doesn't have another resolver in it."""
    return (
        not rv.startswith("https://identifiers.org")
        and not rv.startswith("http://identifiers.org")
        and "n2t.net" not in rv
        and "purl.bioontology.org" not in rv
    )


@lru_cache(maxsize=1)
def get_json_schema():
    """Get the JSON schema for the bioregistry."""
    rv = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "$id": "https://bioregistry.io/schema.json",
    }
    rv.update(
        pydantic.schema.schema(
            [
                Author,
                Collection,
                Provider,
                Resource,
                Registry,
                RegistrySchema,
                Context,
            ],
            title="Bioregistry JSON Schema",
            description="The Bioregistry JSON Schema describes the shapes of the objects in"
            " the registry, metaregistry, collections, and their other related"
            " resources",
        )
    )
    return rv


def main():
    """Dump the JSON schemata."""
    with SCHEMA_PATH.open("w") as file:
        json.dump(get_json_schema(), indent=2, fp=file)


if __name__ == "__main__":
    main()
