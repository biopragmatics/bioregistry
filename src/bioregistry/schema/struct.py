# -*- coding: utf-8 -*-

"""Pydantic models for the Bioregistry."""

import itertools as itt
import json
import logging
import pathlib
import re
import textwrap
from collections import defaultdict
from functools import lru_cache
from operator import attrgetter
from typing import (
    Any,
    Callable,
    ClassVar,
    Dict,
    Iterable,
    List,
    Mapping,
    Optional,
    Sequence,
    Set,
    Tuple,
    Union,
    cast,
)

import pydantic.schema
from pydantic import BaseModel, Field

from bioregistry import constants as brc
from bioregistry.constants import BIOREGISTRY_REMOTE_URL, DOCS, URI_FORMAT_KEY
from bioregistry.license_standardizer import standardize_license
from bioregistry.schema.utils import EMAIL_RE
from bioregistry.utils import curie_to_str, removeprefix, removesuffix

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
BULK_UPLOAD_FORM = DOCS.joinpath("bulk_prefix_request_template.tsv")

#: Search string for skipping formatters containing this
IDOT_SKIP = "identifiers.org"


def _uri_sort(uri):
    try:
        protocol, rest = uri.split(":", 1)
    except ValueError:
        return uri, ""
    return rest, protocol


def _yield_protocol_variations(u):
    if u.startswith("http://"):
        yield "https://" + u[7:]
        yield u
    elif u.startswith("https://"):
        yield u
        yield "http://" + u[8:]
    else:
        yield u


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

URI_FORMAT_PATHS = [
    ("miriam", URI_FORMAT_KEY),
    ("n2t", URI_FORMAT_KEY),
    ("go", URI_FORMAT_KEY),
    ("biocontext", URI_FORMAT_KEY),
    ("wikidata", URI_FORMAT_KEY),
    ("uniprot", URI_FORMAT_KEY),
    ("cellosaurus", URI_FORMAT_KEY),
]


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


class Publication(BaseModel):
    """Metadata about a publication."""

    pubmed: Optional[str] = Field(
        title="PubMed", description="The PubMed identifier for the article"
    )
    doi: Optional[str] = Field(
        title="DOI",
        description="The DOI for the article. DOIs are case insensitive, so these are "
        "required by the Bioregistry to be standardized to their lowercase form.",
    )
    pmc: Optional[str] = Field(
        title="PMC", description="The PubMed Central identifier for the article"
    )
    title: Optional[str] = Field(description="The title of the article")

    def key(self) -> Tuple[str, ...]:
        """Create a key based on identifiers in this data structure."""
        return self.pubmed or "", self.doi or "", self.pmc or ""

    def get_url(self) -> str:
        """Get a URL link."""
        for prefix, identifier in [
            ("pubmed", self.pubmed),
            ("doi", self.doi),
            ("pmc", self.pmc),
        ]:
            if identifier is not None:
                return f"https://bioregistry.io/{prefix}:{identifier}"
        raise ValueError("no fields were full")


class Resource(BaseModel):
    """Metadata about an ontology, database, or other resource."""

    prefix: str = Field(
        ...,
        description="The prefix for this resource",
        exclude=True,
        integration_status="required",
    )
    name: Optional[str] = Field(
        description="The name of the resource", integration_status="required"
    )
    description: Optional[str] = Field(
        description="A description of the resource", integration_status="required"
    )
    pattern: Optional[str] = Field(
        description="The regular expression pattern for local unique identifiers in the resource",
        integration_status="required_for_new",
    )
    uri_format: Optional[str] = Field(
        title="URI format string",
        description="The URI format string, which must have at least one ``$1`` in it",
        integration_status="required_for_new",
    )
    providers: Optional[List[Provider]] = Field(
        description="Additional, non-default providers for the resource",
    )
    homepage: Optional[str] = Field(
        description="The URL for the homepage of the resource, preferably using HTTPS",
        integration_status="required",
    )
    repository: Optional[str] = Field(
        description="The URL for the repository of the resource",
    )
    contact: Optional[Attributable] = Field(
        description=(
            "The contact email address for the resource. This must correspond to a specific "
            "person and not be a listserve nor a shared email account."
        ),
        integration_status="suggested",
    )
    example: Optional[str] = Field(
        description="An example local identifier for the resource, explicitly excluding any redundant "
        "usage of the prefix in the identifier. For example, a GO identifier should only "
        "look like ``1234567`` and not like ``GO:1234567``",
        integration_status="required",
    )
    example_extras: Optional[List[str]] = Field(
        description="Extra example identifiers",
    )
    example_decoys: Optional[List[str]] = Field(
        description="Extra example identifiers that explicitly fail regex tests",
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
    download_rdf: Optional[str] = Field(
        title="RDF Download URL",
        description=_dedent(
            """
    The URL to download the resource as an RDF file, in one of many formats.
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
    banana_peel: Optional[str] = Field(description="Delimiter used in banana")
    deprecated: Optional[bool] = Field(
        description=_dedent(
            """\
    A flag denoting if this resource is deprecated. Currently, this is a blanket term
    that covers cases when the prefix is no longer maintained, when it has been rolled
    into another resource, when the website related to the resource goes down, or any
    other reason that it's difficult or impossible to find full metadata on the resource.
    If this is set to true, please add a comment explaining why. This flag will override
    annotations from the OLS, OBO Foundry, and others on the deprecation status,
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
    publications: Optional[List[Publication]] = Field(
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
        integration_status="required_for_new",
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
        ),
        integration_status="required_for_new",
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
    twitter: Optional[str] = Field(description="The twitter handle for the project")
    github_request_issue: Optional[int] = Field(
        description="The GitHub issue for the new prefix request"
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
    #: External data from the EcoPortal ontology repository
    ecoportal: Optional[Mapping[str, Any]]
    #: External data from the AgroPortal ontology repository
    agroportal: Optional[Mapping[str, Any]]
    #: External data from the CropOCT ontology curation tool
    cropoct: Optional[Mapping[str, Any]]
    #: External data from the Ontology Lookup Service
    ols: Optional[Mapping[str, Any]]
    #: External data from the AberOWL ontology repository
    aberowl: Optional[Mapping[str, Any]]
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
    #: External data from BioContext
    biocontext: Optional[Mapping[str, Any]]
    #: External data from EDAM ontology
    edam: Optional[Mapping[str, Any]]
    #: External data from re3data
    re3data: Optional[Mapping[str, Any]]

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
        >>> get_resource("chebi").get_mapped_prefix("obofoundry")
        'CHEBI'
        """
        if metaprefix == "obofoundry":
            obofoundry_dict = self.obofoundry or {}
            if "preferredPrefix" in obofoundry_dict:
                return obofoundry_dict["preferredPrefix"]
            if "prefix" in obofoundry_dict:
                return obofoundry_dict["prefix"].upper()
            return None
        return self.get_mappings().get(metaprefix)

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

        >>> get_resource("go").get_banana()
        'GO'
        >>> get_resource("vario").get_banana()
        'VariO'

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
        if self.get_namespace_in_lui() is False:
            return None
        miriam_prefix = self.get_miriam_prefix()
        obo_preferred_prefix = self.get_obo_preferred_prefix()
        if miriam_prefix is not None and obo_preferred_prefix is not None:
            return obo_preferred_prefix
        return None

    def get_banana_peel(self) -> str:
        """Get the delimiter between the banana and the local unique identifier."""
        return ":" if self.banana_peel is None else self.banana_peel

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
        for metaprefix, key in URI_FORMAT_PATHS:
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

    def get_mappings(self) -> Mapping[str, str]:
        """Get the mappings to external registries, if available."""
        return self.mappings or {}

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
            "description",
            ("miriam", "ols", "obofoundry", "wikidata", "fairsharing", "aberowl", "bioportal"),
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
        # FIXME cache this
        return re.compile(pattern)

    def get_pattern_with_banana(self, strict: bool = True) -> Optional[str]:
        r"""Get the pattern for the prefix including a banana if available.

        .. warning::

            This function is meant to mediate backwards compatibility with legacy
            MIRIAM/Identifiers.org standards. New projects should **not** use redundant
            prefixes in their local unique identifiers.

        :param strict: If True (default), and a banana exists for the prefix,
            the banana is required in the pattern. If False, the pattern
            will match the banana if present but will also match the identifier
            without the banana.
        :returns: A pattern for the prefix if available

        >>> import bioregistry as br
        >>> resource = br.get_resource("chebi")

        Strict match requires the banana to be present
        >>> resource.get_pattern_with_banana()
        '^CHEBI:\\d+$'

        Non-strict match allows the banana to be optionally present
        >>> resource.get_pattern_with_banana(strict=False)
        '^(CHEBI:)?\\d+$'
        """
        pattern = self.get_pattern()
        if pattern is None:
            return None
        banana = self.get_banana()
        if not banana:
            return pattern

        banana_peel = self.get_banana_peel()
        prepattern = f"{banana}{banana_peel}"
        if not strict:
            prepattern = f"({prepattern})?"
        return "^" + prepattern + pattern.lstrip("^")

    def get_pattern_re_with_banana(self, strict: bool = True):
        """Get the compiled pattern for the prefix including a banana if available.

        .. warning::

            This function is meant to mediate backwards compatibility with legacy
            MIRIAM/Identifiers.org standards. New projects should **not** use redundant
            prefixes in their local unique identifiers.

        :param strict: If True (default), and a banana exists for the prefix,
            the banana is required in the pattern. If False, the pattern
            will match the banana if present but will also match the identifier
            without the banana.
        :returns: A compiled pattern for the prefix if available

        >>> import bioregistry as br
        >>> resource = br.get_resource("chebi")

        Strict match requires banana
        >>> resource.get_pattern_re_with_banana().match("1234")

        >>> resource.get_pattern_re_with_banana().match("CHEBI:1234")
        <re.Match object; span=(0, 10), match='CHEBI:1234'>

        Loose match does not require banana
        >>> resource.get_pattern_re_with_banana(strict=False).match('1234')
        <re.Match object; span=(0, 4), match='1234'>
        >>> resource.get_pattern_re_with_banana(strict=False).match('CHEBI:1234')
        <re.Match object; span=(0, 10), match='CHEBI:1234'>
        """
        p = self.get_pattern_with_banana(strict=strict)
        if p is None:
            return None
        return re.compile(p)

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
        # TODO go through more external data looking for this
        example = self.get_external("ncbi").get("example")
        if example is not None:
            return example
        return None

    def get_examples(self) -> List[str]:
        """Get a list of examples."""
        rv = []
        example = self.get_example()
        if example:
            rv.append(example)
        rv.extend(self.example_extras or [])
        return rv

    def get_example_curie(self, use_preferred: bool = False) -> Optional[str]:
        """Get an example CURIE, if an example identifier is available.

        :param use_preferred: Should the preferred prefix be used instead
            of the Bioregistry prefix (if it exists)?
        :return: An example CURIE for this resource
        """
        example = self.get_example()
        if example is None:
            return None
        return self.get_curie(example, use_preferred=use_preferred)

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

    def get_publications(self) -> List[Publication]:
        """Get a list of publications."""
        publications = self.publications or []
        if self.obofoundry:
            for publication in self.obofoundry.get("publications", []):
                url, title = publication["id"], publication["title"]
                if url.startswith("https://www.ncbi.nlm.nih.gov/pubmed/"):
                    pubmed = url[len("https://www.ncbi.nlm.nih.gov/pubmed/") :]
                    publications.append(Publication(pubmed=pubmed, title=title, doi=None, pmc=None))
                elif url.startswith("https://doi.org/"):
                    doi = url[len("https://doi.org/") :]
                    publications.append(
                        Publication(doi=doi.lower(), title=title, pubmed=None, pmc=None)
                    )
                elif url.startswith("https://www.medrxiv.org/content/"):
                    doi = url[len("https://www.medrxiv.org/content/") :]
                    publications.append(
                        Publication(doi=doi.lower(), title=title, pubmed=None, pmc=None)
                    )
                elif url.startswith("https://zenodo.org/record/"):
                    continue
                elif "ceur-ws.org" in url:
                    continue
                else:
                    logger.warning("unhandled obo foundry publication ID: %s", url)
        if self.fairsharing:
            for publication in self.fairsharing.get("publications", []):
                pubmed = publication.get("pubmed_id")
                doi = publication.get("doi")
                title = publication.get("title")
                if pubmed or doi:
                    publications.append(
                        Publication(pubmed=pubmed, doi=doi and doi.lower(), title=title, pmc=None)
                    )
        if self.prefixcommons:
            for pubmed in self.prefixcommons.get("pubmed_ids", []):
                publications.append(Publication(pubmed=pubmed, doi=None, pmc=None, title=None))
        return deduplicate_publications(publications)

    def get_twitter(self) -> Optional[str]:
        """Get the Twitter handle for ther resource."""
        if self.twitter:
            return self.twitter
        if self.obofoundry:
            return self.obofoundry.get("twitter")
        return None

    def get_obofoundry_prefix(self) -> Optional[str]:
        """Get the OBO Foundry prefix if available.

        :returns: The OBO prefix, if available.

        >>> from bioregistry import get_resource
        >>> get_resource("go").get_obofoundry_prefix()  # standard
        'GO'
        >>> get_resource("aao").get_obofoundry_prefix()  # standard but deprecated
        'AAO'
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

    def get_biocontext_uri_format(self) -> Optional[str]:
        """Get the BioContext URI format string for this entry, if available.

        :returns: The BioContext URI format string, if available.

        >>> from bioregistry import get_resource
        >>> get_resource("hgmd").get_biocontext_uri_format()
        'http://www.hgmd.cf.ac.uk/ac/gene.php?gene=$1'
        """
        return self.get_external("biocontext").get(URI_FORMAT_KEY)

    def get_prefixcommons_uri_format(self) -> Optional[str]:
        """Get the Prefix Commons URI format string for this entry, if available.

        :returns: The Prefix Commons URI format string, if available.

        >>> from bioregistry import get_resource
        >>> get_resource("antweb").get_prefixcommons_uri_format()
        'http://www.antweb.org/specimen.do?name=$1'
        """
        return self.get_external("prefixcommons").get(URI_FORMAT_KEY)

    def get_identifiers_org_prefix(self) -> Optional[str]:
        """Get the MIRIAM/Identifiers.org prefix, if available.

        :returns: The Identifiers.org/MIRIAM prefix corresponding to the prefix, if mappable.

        >>> from bioregistry import get_resource
        >>> get_resource('chebi').get_identifiers_org_prefix()
        'chebi'
        >>> get_resource('ncbitaxon').get_identifiers_org_prefix()
        'taxonomy'
        >>> assert get_resource('MONDO').get_identifiers_org_prefix() is None
        """
        return self.get_mapped_prefix("miriam")

    def get_miriam_prefix(self):
        """Get the MIRIAM/Identifiers.org prefix, if available."""
        return self.get_identifiers_org_prefix()

    def get_miriam_uri_prefix(
        self, legacy_delimiter: bool = False, legacy_protocol: bool = False
    ) -> Optional[str]:
        """Get the Identifiers.org URI prefix for this entry, if possible.

        :param legacy_protocol: If true, uses HTTP
        :param legacy_delimiter: If true, uses a slash delimiter for CURIEs instead of colon
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
        protocol = "http" if legacy_protocol else "https"
        delimiter = "/" if legacy_delimiter else ":"
        return f"{protocol}://identifiers.org/{miriam_prefix}{delimiter}"

    def get_miriam_uri_format(
        self, legacy_delimiter: bool = False, legacy_protocol: bool = False
    ) -> Optional[str]:
        """Get the Identifiers.org URI format string for this entry, if possible.

        :param legacy_protocol: If true, uses HTTP
        :param legacy_delimiter: If true, uses a slash delimiter for CURIEs instead of colon
        :returns: The Identifiers.org/MIRIAM URL format string, if available.

        >>> from bioregistry import get_resource
        >>> get_resource('ncbitaxon').get_miriam_uri_format()
        'https://identifiers.org/taxonomy:$1'
        >>> get_resource('go').get_miriam_uri_format()
        'https://identifiers.org/GO:$1'
        >>> assert get_resource('sty').get_miriam_uri_format() is None
        """
        miriam_url_prefix = self.get_miriam_uri_prefix(
            legacy_delimiter=legacy_delimiter, legacy_protocol=legacy_protocol
        )
        if miriam_url_prefix is None:
            return None
        return f"{miriam_url_prefix}$1"

    def get_nt2_uri_prefix(self, legacy_protocol: bool = False) -> Optional[str]:
        """Get the Name-to-Thing URI prefix for this entry, if possible."""
        n2t_prefix = self.get_mapped_prefix("n2t")
        if n2t_prefix is None:
            return None
        protocol = "http" if legacy_protocol else "https"
        return f"{protocol}://n2t.net/{n2t_prefix}:"

    def get_n2t_uri_format(self, legacy_protocol: bool = False):
        """Get the Name-to-Thing URI format string, if available."""
        n2t_uri_prefix = self.get_nt2_uri_prefix(legacy_protocol=legacy_protocol)
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
        "biocontext": get_biocontext_uri_format,
        "miriam": get_miriam_uri_format,
        "n2t": get_n2t_uri_format,
        "ols": get_ols_uri_format,
    }

    DEFAULT_URI_FORMATTER_PRIORITY: ClassVar[Sequence[str]] = (
        "default",
        "obofoundry",
        "biocontext",
        "miriam",
        "n2t",
        "ols",
        "prefixcommons",
    )

    def get_uri_format(self, priority: Optional[Sequence[str]] = None) -> Optional[str]:
        """Get the URI format string for the given prefix, if it's available.

        :param priority: The priority order of metaresources to use for format URI lookup.
            The default is:

            1. Default first party (from the Bioregistry, BioContext, or MIRIAM)
            2. OBO Foundry
            3. BioContext
            4. MIRIAM/Identifiers.org
            5. N2T
            6. OLS
            7. Prefix Commons

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
        >>> priority = ['obofoundry', 'bioregistry', 'biocontext', 'miriam', 'ols']
        >>> get_resource("chebi").get_uri_format(priority=priority)
        'http://purl.obolibrary.org/obo/CHEBI_$1'
        """
        # TODO add examples in doctests for BioContext, MIRIAM/Identifiers.org, and OLS
        for metaprefix in priority or self.DEFAULT_URI_FORMATTER_PRIORITY:
            formatter = self.URI_FORMATTERS.get(metaprefix)
            if formatter is None:
                logger.warning("could not get formatter for %s", metaprefix)
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

    def get_uri_formats(self) -> Set[str]:
        """Get all URI prefixes."""
        uri_formats = itt.chain.from_iterable(
            _yield_protocol_variations(uri_format) for uri_format in self._iter_uri_formats()
        )
        return set(sorted(uri_formats, key=_uri_sort))

    def _iter_uri_formats(self) -> Iterable[str]:
        if self.uri_format:
            yield self.uri_format
        yield f"https://bioregistry.io/{self.prefix}:$1"
        preferred_prefix = self.get_preferred_prefix()
        if preferred_prefix:
            yield f"https://bioregistry.io/{preferred_prefix}:$1"
        for synonym in self.get_synonyms():
            yield f"https://bioregistry.io/{synonym}:$1"
        # TODO consider adding bananas
        for provider in self.get_extra_providers():
            yield provider.uri_format
        for formatter_getter in self.URI_FORMATTERS.values():
            uri_format = formatter_getter(self)
            if uri_format:
                yield uri_format
        for metaprefix, key in URI_FORMAT_PATHS:
            uri_format = self.get_external(metaprefix).get(key)
            if uri_format:
                yield uri_format
        miriam_legacy_uri_prefix = self.get_miriam_uri_format(legacy_delimiter=True)
        if miriam_legacy_uri_prefix:
            yield miriam_legacy_uri_prefix

    def get_extra_providers(self) -> List[Provider]:
        """Get a list of all extra providers."""
        rv = []
        if self.providers is not None:
            rv.extend(self.providers)
        if self.miriam:
            for p in self.miriam.get("providers", []):
                rv.append(Provider(**p))
        return sorted(rv, key=attrgetter("code"))

    def get_curie(self, identifier: str, use_preferred: bool = False) -> str:
        """Get a CURIE for a local unique identifier in this resource's semantic space.

        :param identifier: A local unique identifier in this resource's semantic space
        :param use_preferred: Should preferred prefixes be used? Set this to true if you're in the OBO context.
        :returns: A CURIE for the given identifier

        >>> import bioregistry
        >>> resource = bioregistry.get_resource("go")
        >>> resource.get_curie("0000001")
        'go:0000001'
        >>> resource.get_curie("0000001", use_preferred=True)
        'GO:0000001'
        """
        _p = self.get_preferred_prefix() or self.prefix if use_preferred else self.prefix
        return curie_to_str(_p, identifier)

    def standardize_identifier(self, identifier: str) -> str:
        """Normalize the identifier to not have a redundant prefix or banana.

        :param identifier: The identifier in the CURIE
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
        peel = self.get_banana_peel()
        prebanana = f"{banana}{peel}".casefold()
        icf = identifier.casefold()
        if banana and icf.startswith(prebanana):
            return identifier[len(prebanana) :]
        elif icf.startswith(f"{self.prefix.casefold()}{peel}"):
            return identifier[len(self.prefix) + len(peel) :]
        return identifier

    def get_miriam_curie(self, identifier: str) -> Optional[str]:
        """Get the MIRIAM-flavored CURIE."""
        miriam_prefix = self.get_miriam_prefix()
        if miriam_prefix is None:
            return None
        identifier = self.standardize_identifier(identifier)
        if identifier is None:
            return None
        # A "banana" is an embedded prefix that isn't actually part of the identifier.
        # Usually this corresponds to the prefix itself, with some specific stylization
        # such as in the case of FBbt. The banana does NOT include a colon ":" at the end
        banana = self.get_banana()
        if banana:
            peel = self.get_banana_peel()
            processed_banana = f"{banana}{peel}"
            if not identifier.startswith(processed_banana):
                identifier = f"{processed_banana}{identifier}"
            # here we're using the fact that the banana peel has been annotated explicitly
            # to mean that it should be redundant
            if self.banana_peel is None:
                return identifier
        return f"{miriam_prefix}:{identifier}"

    def miriam_standardize_identifier(self, identifier: str) -> Optional[str]:
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
        >>> get_resource("go").miriam_standardize_identifier('0000001')
        'GO:0000001'
        >>> get_resource("go").miriam_standardize_identifier('GO:0000001')
        'GO:0000001'

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
        if self.get_miriam_prefix() is None:
            return None
        # A "banana" is an embedded prefix that isn't actually part of the identifier.
        # Usually this corresponds to the prefix itself, with some specific stylization
        # such as in the case of FBbt. The banana does NOT include a colon ":" at the end
        banana = self.get_banana()
        if banana:
            delimiter = self.get_banana_peel()
            processed_banana = f"{banana}{delimiter}"
            if not identifier.startswith(processed_banana):
                return f"{processed_banana}{identifier}"
        return identifier

    def is_valid_identifier(self, identifier: str) -> bool:
        """Check that a local unique identifier is canonical, meaning no bananas."""
        pattern = self.get_pattern_re()
        if pattern is None:
            return True
        return pattern.fullmatch(identifier) is not None

    def is_standardizable_identifier(self, identifier: str) -> bool:
        """Check that a local unique identifier can be normalized and also matches a prefix's pattern."""
        return self.is_valid_identifier(self.standardize_identifier(identifier))

    def get_download_obo(self) -> Optional[str]:
        """Get the download link for the latest OBO file.

        :return: A URL for an OBO text file download, if exists.

        Get an ontology download link annotated directly in the
        Bioregistry:

        >>> from bioregistry import get_resource
        >>> get_resource("caloha").get_download_obo()
        'https://download.nextprot.org/pub/current_release/controlled_vocabularies/caloha.obo'

        Get an ontology download link from the OBO Foundry:

        >>> get_resource("bfo").get_download_obo()
        'http://purl.obolibrary.org/obo/bfo.obo'

        Get ontology download link in AberOWL but not OBO Foundry
        (note this might change over time so the exact value isn't
        used in the doctest):

        >>> url = get_resource("dermo").get_download_obo()
        >>> assert url is not None and url.startswith("http://aber-owl.net/media/ontologies/DERMO")
        """
        if self.download_obo:
            return self.download_obo
        return self.get_external("obofoundry").get("download.obo") or self.get_external(
            "aberowl"
        ).get("download_obo")

    def get_download_obograph(self) -> Optional[str]:
        """Get the download link for the latest OBOGraph JSON file."""
        if self.download_json:
            return self.download_json
        return self.get_external("obofoundry").get("download.json")

    def get_download_rdf(self) -> Optional[str]:
        """Get the download link for the latest RDF file."""
        return self.download_rdf

    def get_download_owl(self) -> Optional[str]:
        """Get the download link for the latest OWL file.

        :return: A URL for an OWL file download, if exists.

        Get an ontology download link annotated directly in the
        Bioregistry:

        >>> from bioregistry import get_resource
        >>> get_resource("orphanet.ordo").get_download_owl()
        'http://www.orphadata.org/data/ORDO/ordo_orphanet.owl'

        Get an ontology download link from the OBO Foundry:

        >>> get_resource("mod").get_download_owl()
        'http://purl.obolibrary.org/obo/mod.owl'

        Get ontology download link in AberOWL but not OBO Foundry
        (note this might change over time so the exact value isn't
        used in the doctest):

        >>> url = get_resource("birnlex").get_download_owl()
        >>> assert url is not None and url.startswith("http://aber-owl.net/media/ontologies/BIRNLEX/")

        """
        if self.download_owl:
            return self.download_owl
        return (
            self.get_external("obofoundry").get("download.owl")
            or self.get_external("ols").get("version.iri")
            or self.get_external("ols").get("download")
            or self.get_external("aberowl").get("download_owl")
        )

    def has_download(self) -> bool:
        """Check if this resource can be downloaded."""
        return any(
            (
                self.get_download_obo(),
                self.get_download_owl(),
                self.get_download_obograph(),
            )
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

    def get_short_description(self, use_markdown: bool = False) -> Optional[str]:
        """Get a short description."""
        desc = self.get_description()
        if not desc:
            return None
        ss = desc.split(". ")
        if ss:
            rv = ss[0].rstrip(".") + "."
        else:
            rv = desc.rstrip(".") + "."
            logger.warning("could not split description: %s", desc)
        if not use_markdown:
            return rv

        import markupsafe
        from markdown import markdown

        rv = cast(str, removesuffix(removeprefix(markdown(rv), "<p>"), "</p>"))
        return markupsafe.Markup(rv)


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


class RegistryGovernance(BaseModel):
    """Metadata about a registry's governance."""

    curation: Literal["private", "import", "community", "opaque-review", "open-review"]
    curates: bool = Field(description="Does the registry curate novel prefixes?")
    imports: bool = Field(
        description="Does the registry import and align prefixes from other registries?"
    )
    scope: str = Field(
        description="What is the scope of prefixes which the registry covers? For example,"
        " some registries are limited to ontologies, some have a full scope over the life sciences,"
        " and some are general purpose."
    )
    comments: Optional[str]
    accepts_external_contributions: bool = Field(
        description="Does the registry (in theory) accept external contributions, either via suggestion or"
        " proactive improvement? This field does not pass judgement on the difficult of this"
        " process from the perspective of the submitter nor the responsiveness of the registry."
        " This field does not consider the ability for insiders (i.e., people with private relationships"
        " to the maintainers) to affect change."
    )
    public_version_control: bool = Field(
        description="Does the registry store its data/code in publicly available version control"
        " system, such as GitHub or GitLab? Currently there is no resource that does one but not"
        " the other, so this is grouped (for now)."
    )
    review_team: Literal["public", "inferrable", "private", "n/a"] = Field(
        description="Are the reviewers for external contributions known? If there's a well-defined,"
        " maintained listing, then it can be marked as public. If it can be inferred, e.g. from reading"
        " the commit history on a version control system, then it can be marked as inferrable. A closed"
        " review team, e.g., like for Identifiers.org can be marked as private. Resources that do not"
        " accept external contributions can be marked with N/A."
    )
    status: Literal["active", "unresponsive", "inactive"] = Field(
        description="What is the status of the repository? An active repository is still being maintained and also"
        " is responsive to external requests for improvement. An unresponsive repository is still being maintained"
        " in some capacity but is not responsive to external requests for improvement. An inactive repository is"
        " no longer being proactively maintained (though may receive occasional patches)."
    )

    @property
    def review_team_icon(self) -> str:
        """Get an icon for the review team."""
        if self.review_team == "public":
            return "✓"
        elif self.review_team == "inferrable":
            return "✓*"
        elif self.review_team == "private":
            return "✗"
        else:
            return ""


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
        ...,
        description="Does this registry provide a URL into which a search"
        " query can be formatted to show a list of results?",
    )
    fair: bool = Field(
        ...,
        description="Does this registry provide a structured bulk dump of its prefixes, records,"
        " and all associated metadata in an easily findable and accessible manner?",
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
    governance: RegistryGovernance = Field(
        ..., description="A structured description of the governance for the registry"
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
    short_name: Optional[str] = Field(
        description="A short name for the resource, e.g., for use in charts"
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

    def get_short_name(self) -> str:
        """Get the short name or full name if none annotated."""
        return self.short_name or self.name

    @property
    def is_resolver(self) -> bool:
        """Check if it is a resolver."""
        return self.resolver_uri_format is not None and self.resolver_type != "lookup"

    @property
    def is_lookup(self) -> bool:
        """Check if it is a lookup service."""
        return self.resolver_uri_format is not None and self.resolver_type == "lookup"


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

    def as_context_jsonld_str(self) -> str:
        """Get the JSON-LD context as a string from a given collection."""
        return json.dumps(self.as_context_jsonld())

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
    blacklist: Optional[List[str]] = Field(
        ...,
        description="This is a list of canonical Bioregistry prefixes that should not be included in the context.",
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
                Publication,
            ],
            title="Bioregistry JSON Schema",
            description="The Bioregistry JSON Schema describes the shapes of the objects in"
            " the registry, metaregistry, collections, and their other related"
            " resources",
        )
    )
    return rv


def write_bulk_prefix_request_template():
    """Write a template for bulk prefix requests."""
    import bioregistry

    required = []
    optional = []

    metaprefixes = set(bioregistry.read_metaregistry())

    for name, field in Resource.__fields__.items():
        if name in {
            "providers",
            "example_extras",
            "example_decoys",
            "contributor_extras",
            "mappings",
            "reviewer",
            "contact",
            "contributor",
            "github_request_issue",
            "banana_peel",
            "publications",
        }:
            continue
        if name in metaprefixes:
            continue
        status = field.field_info.extra.get("integration_status", "optional")
        if status in {"required", "required_for_new"}:
            required.append(name)
        elif status == "skip":
            continue
        else:
            optional.append(name)
    required.extend(
        ("contributor_name", "contributor_github", "contributor_orcid", "contributor_email")
    )
    optional.extend(("contact_name", "contact_github", "contact_orcid", "contact_email"))

    with BULK_UPLOAD_FORM.open("w") as file:
        print(  # noqa:T201
            "request_id",
            *required,
            *(f"{c} (optional)" for c in optional),
            sep="\t",
            file=file,
        )
        # add examples
        for i, prefix in enumerate(["chebi", "tkg", "mondo", "nmdc"], start=1):
            resource = bioregistry.get_resource(prefix)
            assert resource is not None
            print(  # noqa:T201
                f"example_{i} (delete this row)",
                *(_get(resource, c) for c in required),
                *(_get(resource, c) for c in optional),
                sep="\t",
                file=file,
            )
        for i in range(1, 6):
            print(i, *[""] * (len(required) + len(optional)), sep="\t", file=file)  # noqa:T201


def _get(resource, key):
    getter_key = f"get_{key}"
    if hasattr(resource, getter_key):
        x = getattr(resource, getter_key)()
    elif hasattr(resource, key):
        x = getattr(resource, key)
    elif "_" in key:
        k1, k2 = key.split("_")
        x1 = getattr(resource, k1, None)
        x = getattr(x1, k2, None) if x1 is not None else None
    else:
        x = None
    if isinstance(x, (list, set)):
        return "|".join(sorted(x))
    return x or ""


def deduplicate_publications(publications: List[Publication]) -> List[Publication]:
    """Deduplicate publications."""
    d = defaultdict(list)

    # Index mappings
    doi_to_pmid = {}
    pmid_to_doi = {}
    doi_to_pmc = {}
    pmc_to_doi = {}
    pmid_to_pmc = {}
    pmc_to_pmid = {}
    for p in publications:
        if p.doi and p.pubmed:
            doi_to_pmid[p.doi] = p.pubmed
            pmid_to_doi[p.pubmed] = p.doi
        if p.doi and p.pmc:
            doi_to_pmc[p.doi] = p.pmc
            pmc_to_doi[p.pmc] = p.doi
        if p.pubmed and p.pmc:
            pmid_to_pmc[p.pubmed] = p.pmc
            pmc_to_pmid[p.pmc] = p.pubmed
    for p in publications:
        # apply mappings
        if p.doi and not p.pubmed:
            p.pubmed = doi_to_pmid.get(p.doi)
        if p.pubmed and not p.doi:
            p.doi = pmid_to_doi.get(p.pubmed)
        if p.doi and not p.pmc:
            p.pmc = doi_to_pmc.get(p.doi)
        if p.pubmed and not p.pmc:
            p.pmc = pmid_to_pmc.get(p.pubmed)
        # todo not exhaustive, doesn't account for multi-hop mappings
        d[p.key()].append(p)

    for vs in d.values():
        try:
            title = next(v.title for v in vs if v.title)
        except StopIteration:
            continue
        else:
            vs[0].title = title
    return [v[0] for _, v in sorted(d.items())]


def main():
    """Dump the JSON schemata."""
    write_bulk_prefix_request_template()

    with SCHEMA_PATH.open("w") as file:
        json.dump(get_json_schema(), indent=2, fp=file)


if __name__ == "__main__":
    main()
