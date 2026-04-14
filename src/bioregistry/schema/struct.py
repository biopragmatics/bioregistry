"""Pydantic models for the Bioregistry."""

from __future__ import annotations

import itertools as itt
import json
import logging
import pathlib
import re
import typing
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass
from functools import lru_cache
from operator import attrgetter
from typing import (
    TYPE_CHECKING,
    Annotated,
    Any,
    ClassVar,
    Generic,
    Literal,
    TypeAlias,
    TypeVar,
    cast,
    overload,
)

import click
from curies import Reference
from curies.w3c import NCNAME_RE
from pydantic import BaseModel, EmailStr, Field, PrivateAttr
from pydantic.json_schema import models_json_schema
from typing_extensions import Self

from bioregistry import constants as brc
from bioregistry.constants import (
    BIOREGISTRY_REMOTE_URL,
    DOCS,
    MIRIAM_NAMESPACE_IN_LUI,
    ORCID_FIELD,
    URI_FORMAT_KEY,
    WIKIDATA_FIELD,
    _dedent,
)
from bioregistry.license_standardizer import standardize_license
from bioregistry.utils import curie_to_str, deduplicate, removeprefix, removesuffix

if TYPE_CHECKING:
    import rdflib
    import rdflib.term

__all__ = [
    "AnnotatedURL",
    "Attributable",
    "Author",
    "Collection",
    "Context",
    "Organization",
    "Provider",
    "Publication",
    "RDFFormat",
    "Registry",
    "Resource",
    "ResourceStatus",
    "StatusCheck",
    "deduplicate_publications",
    "filter_collections",
    "get_json_schema",
]

logger = logging.getLogger(__name__)

HERE = pathlib.Path(__file__).parent.resolve()
SCHEMA_PATH = HERE.joinpath("schema.json")
BULK_UPLOAD_FORM = DOCS.joinpath("bulk_prefix_request_template.tsv")

#: Search string for skipping formatters containing this
IDOT_SKIP = "identifiers.org"
ORCID_TO_GITHUB = {
    "0000-0003-0530-4305": "essepuntato",
    "0000-0002-9903-4248": "mbaudis",
    "0000-0001-9018-4680": "alimanfoo",
}

URI_IRI_INFO = (
    "Note that this field is generic enough to accept IRIs. "
    "See the URI specification (https://www.rfc-editor.org/rfc/rfc3986) "
    "and IRI specification (https://www.ietf.org/rfc/rfc3987.txt) for more information."
)

X = TypeVar("X")

#: A controlled vocabulary of domains.
Domain: TypeAlias = Literal[
    "chemical",
    "tissue",
    "reaction",
    "gene",
    "cell and cell line",
    "cellular component",
    "model",
    "metabolite",
    "organization",
    "clinical trial",
    "pathway",
    "protein family",
    "gene family",
    "disease",
    "data model",
    "vaccine",
    "multiple",
    "variant",
    "publication",
    "protein complex",
    "mirna",
    "taxonomy",
    "project",
    "grant",
    "classification",
    "protein",
    "study",
    "relationship",
    "relationship type",
    "antibody",
    "peptide",
    "schema",
    "strain",
    "license",
    "semantic web",
    "geography",
    "assay",
    "ptm",
    "bibliometrics",
    "experiment",
    "genetic code",
    "mathematics",
]


def _uri_sort(uri: str) -> tuple[str, str]:
    try:
        protocol, rest = uri.split(":", 1)
    except ValueError:
        return uri, ""
    return rest, protocol


def _yield_protocol_variations(u: str) -> Iterable[str]:
    if u.startswith("http://"):
        yield "https://" + u[7:]
        yield u
    elif u.startswith("https://"):
        yield u
        yield "http://" + u[8:]
    else:
        yield u


URI_FORMAT_PATHS = [
    ("miriam", URI_FORMAT_KEY),
    ("n2t", URI_FORMAT_KEY),
    ("go", URI_FORMAT_KEY),
    ("biocontext", URI_FORMAT_KEY),
    ("wikidata", URI_FORMAT_KEY),
    ("uniprot", URI_FORMAT_KEY),
    ("cellosaurus", URI_FORMAT_KEY),
    ("prefixcommons", URI_FORMAT_KEY),
    ("rrid", URI_FORMAT_KEY),
    ("tib", URI_FORMAT_KEY),
    ("bartoc", URI_FORMAT_KEY),
]


@dataclass
class MetaprefixAnnotatedValue(Generic[X]):
    """A value with its metaprefix as provenance."""

    value: X
    metaprefix: str


class Organization(BaseModel):
    """Model for organizations."""

    ror: str | None = Field(
        default=None,
        title="Research Organization Registry identifier",
        description="ROR identifier for a record about the organization",
    )
    wikidata: Annotated[str | None, WIKIDATA_FIELD] = None
    gnd: str | None = Field(
        default=None, title="Gemeinsame Normdatei (Integrated Authority File) identifier"
    )
    name: str = Field(..., description="Name of the organization")
    partnered: bool = Field(
        False, description="Has this organization made a specific connection with Bioregistry?"
    )

    @property
    def pair(self) -> tuple[str, str]:
        """Get a CURIE pair."""
        if self.ror:
            return "ror", self.ror
        elif self.wikidata:
            return "wikidata", self.wikidata
        elif self.gnd:
            return "gnd", self.gnd
        raise ValueError

    @property
    def link(self) -> str:
        """Get a link for the organization."""
        if self.ror:
            return f"https://ror.org/{self.ror}"
        elif self.wikidata:
            return f"https://scholia.toolforge.org/{self.wikidata}"
        elif self.gnd:
            return f"https://d-nb.info/gnd/{self.gnd}"
        else:
            raise ValueError


class Attributable(BaseModel):
    """An upper-level metadata for a researcher."""

    name: str = Field(..., description="The full name of the researcher")

    orcid: Annotated[str | None, ORCID_FIELD] = None
    email: EmailStr | None = Field(
        default=None,
        title="Email address",
        description="The email address specific to the researcher.",
    )

    #: The GitHub handle for the author
    github: str | None = Field(
        default=None,
        title="GitHub handle",
        description=_dedent(
            """\
    The GitHub handle enables contacting the researcher on GitHub:
    the *de facto* version control in the computer sciences and life sciences.
    """
        ),
    )

    wikidata: Annotated[str | None, WIKIDATA_FIELD] = None

    def get_score(self) -> int:
        """Get a score."""
        return sum(
            (
                3 * (self.orcid is not None),
                self.email is not None,
                self.github is not None,
                self.wikidata is not None,
            )
        )

    def add_triples(self, graph: rdflib.Graph) -> rdflib.term.Node:
        """Add triples to an RDF graph for this author.

        :param graph: An RDF graph

        :returns: The RDF node representing this author using an ORCiD URI.
        """
        from rdflib import BNode, Literal, Node
        from rdflib.namespace import FOAF, RDFS

        if not self.orcid:
            node: Node = BNode()
        else:
            from .constants import orcid

            node = orcid.term(self.orcid)
        graph.add((node, RDFS.label, Literal(self.name)))
        if self.email:
            graph.add((node, FOAF.mbox, Literal(self.email)))
        return node


class Author(Attributable):
    """Metadata for an author."""

    #: This field is redefined on top of :class:`Attributable` to make
    #: it required. Otherwise, it has the same semantics.
    orcid: Annotated[str, ORCID_FIELD]

    @classmethod
    def get_charlie(cls) -> Self:
        """Get an author object representing Charlie."""
        return cls.model_validate(
            {
                "email": "cthoyt@gmail.com",
                "github": "cthoyt",
                "name": "Charles Tapley Hoyt",
                "orcid": "0000-0003-4423-4370",
            }
        )


class Publication(BaseModel):
    """Metadata about a publication."""

    pubmed: str | None = Field(
        default=None, title="PubMed", description="The PubMed identifier for the article"
    )
    doi: str | None = Field(
        default=None,
        title="DOI",
        description="The DOI for the article. DOIs are case insensitive, so these are "
        "required by the Bioregistry to be standardized to their lowercase form.",
    )
    pmc: str | None = Field(
        default=None, title="PMC", description="The PubMed Central identifier for the article"
    )
    arxiv: str | None = Field(
        default=None, title="arXiv", description="The arXiv identifier for the article"
    )
    title: str | None = Field(default=None, description="The title of the article")
    year: int | None = Field(default=None, description="The year the article was published")

    def key(self) -> tuple[str, ...]:
        """Create a key based on identifiers in this data structure."""
        return self.pubmed or "", self.doi or "", self.pmc or "", self.arxiv or ""

    def get_url(self) -> str:
        """Get a URL link."""
        for prefix, identifier in [
            ("pubmed", self.pubmed),
            ("doi", self.doi),
            ("pmc", self.pmc),
            ("arxiv", self.arxiv),
        ]:
            if identifier is not None:
                return f"https://bioregistry.io/{prefix}:{identifier}"
        raise ValueError("no fields were full")

    def _matches_any_field(self, other: Publication) -> bool:
        return (
            (self.pubmed is not None and self.pubmed == other.pubmed)
            or (self.doi is not None and self.doi == other.doi)
            or (self.pmc is not None and self.pmc == other.pmc)
            or (self.arxiv is not None and self.arxiv == other.arxiv)
        )

    def _sort_key(self) -> tuple[int, str, str]:
        return -(self.year or 0), (self.title or "").casefold(), self.get_url()

    def __lt__(self, other: Publication) -> bool:
        if not isinstance(other, Publication):
            raise TypeError
        return self._sort_key() < other._sort_key()


#: The status of a resource.
ResourceStatus: TypeAlias = Literal[
    "available", "moved", "gone", "hijacked", "degraded", "misconfigured"
]
ResourceStatusAvailable: ResourceStatus = "available"


class StatusCheck(BaseModel):
    """A status check."""

    value: ResourceStatus
    date: str = Field(pattern="^\\d{4}-\\d{2}-\\d{2}$")
    contributor: Annotated[str, ORCID_FIELD]
    notes: str | None = None


class Provider(BaseModel):
    """A provider."""

    code: str = Field(..., description="A locally unique code within the prefix for the provider")
    name: str | None = Field(None, description="Name of the provider")
    description: str | None = Field(None, description="Description of the provider")
    homepage: str | None = Field(None, description="Homepage of the provider")
    uri_format: str = Field(
        ...,
        title="URI Format",
        description=f"The URI format string, which must have at least one ``$1`` in it. {URI_IRI_INFO}",
    )
    first_party: bool | None = Field(
        None, description="Annotates whether a provider is from the first-party organization"
    )
    publications: list[Publication] | None = Field(
        default=None,
        description="A list of publications about the provider. See the `indra` provider for `hgnc` for an example.",
    )
    example: str | None = Field(
        default=None,
        description="An example local identifier, specific to the provider. Providing this value is "
        "only necessary if the example associated with the prefix for which this is a provider "
        "is not resolvable by the provider. The example identifier should exclude any redundant "
        "usage of the prefix. For example, a GO identifier should only "
        "look like ``1234567`` and not like ``GO:1234567``",
    )
    status: StatusCheck | None = Field(
        None,
        description="Tracks the status of the provider. If this isn't set, assume that the provider is still active. See discussion in in https://github.com/biopragmatics/bioregistry/issues/1387.",
    )

    def resolve(self, identifier: str) -> str:
        """Resolve the identifier into a URI.

        :param identifier: The identifier in the semantic space

        :returns: The URI for the identifier
        """
        return self.uri_format.replace("$1", identifier)

    def is_known_inactive(self) -> bool:
        """Check if the resource is known to be inactive."""
        if self.status is None:
            return False
        return self.status.value != ResourceStatusAvailable


#: A list of valid RDF formats.
RDFFormat: TypeAlias = Literal["ttl", "rdf", "xml", "n3", "trix", "nt"]


class AnnotatedURL(BaseModel):
    """A URL annotated with its file type and data schema."""

    url: str
    rdf_format: RDFFormat = Field(default="ttl", title="RDF Format")


DEFAULT_METAPREFIX_PRIORITY = [
    "obofoundry",
    "ols",
    "miriam",
    "wikidata",
    "go",
    "ncbi",
    "bioportal",
    "agroportal",
    "ecoportal",
    "n2t",
    "cellosaurus",
    "cropoct",
    "cheminf",
    "edam",
    "prefixcommons",
    "rrid",
    "bartoc",
    "lov",
    "tib",
    "integbio",
    "aberowl",
    "re3data",
    "uniprot",
]


class Resource(BaseModel):
    """Metadata about an ontology, database, or other resource."""

    prefix: str = Field(
        ...,
        description="The prefix for this resource",
    )
    name: str | None = Field(default=None, description="The name of the resource")
    description: str | None = Field(default=None, description="A description of the resource")
    pattern: str | None = Field(
        default=None,
        description="The regular expression pattern for local unique identifiers in the resource",
    )
    uri_format: str | None = Field(
        default=None,
        title="URI format string",
        description=f"The URI format string, which must have at least one ``$1`` in it. {URI_IRI_INFO}",
    )
    uri_format_resolvable: bool | None = Field(
        default=None,
        title="URI format string resolvable",
        description="If false, denotes if the URI format string is known to be not resolvable",
    )
    rdf_uri_format: str | None = Field(
        default=None,
        title="RDF URI format string",
        description=f"The RDF URI format string, which must have at least one ``$1`` in it. {URI_IRI_INFO}",
    )
    providers: list[Provider] | None = Field(
        default=None,
        description="Additional, non-default providers for the resource",
    )
    homepage: str | None = Field(
        default=None, description="The URL for the homepage of the resource, preferably using HTTPS"
    )
    repository: str | None = Field(
        default=None,
        description="The URL for the repository of the resource",
    )
    contact: Attributable | None = Field(
        default=None,
        description=(
            "The contact email address for the resource. This must correspond to a specific "
            "person and not be a listserve nor a shared email account."
        ),
    )
    contact_extras: list[Attributable] | None = Field(
        default=None,
        description="Secondary contacts. It's required to have a primary contact to have this field.",
    )
    contact_group_email: EmailStr | None = Field(
        default=None,
        description="A group contact email (e.g., a mailing list, a shared address) for the project. "
        "It's required to have a primary contact to have this field.",
    )
    contact_page: str | None = Field(
        default=None,
        description="A URL for a web page that has contact information, e.g., containing a contact form. "
        "It's required to have a primary contact to have this field, even if the primary contact isn't the "
        "preferred mechanism for contact. Only curate this field if a direct email is not available, as this "
        "is the least transparent option for contact.",
    )
    owners: list[Organization] | None = Field(
        default=None,
        description="The owner of the corresponding identifier space. See also https://github.com/biopragmatics/"
        "bioregistry/issues/755.",
    )
    example: str | None = Field(
        default=None,
        description="An example local identifier for the resource, explicitly excluding any redundant "
        "usage of the prefix in the identifier. For example, a GO identifier should only "
        "look like ``1234567`` and not like ``GO:1234567``",
    )
    example_extras: list[str] | None = Field(
        default=None,
        description="Extra example identifiers",
    )
    example_decoys: list[str] | None = Field(
        default=None,
        description="Extra example identifiers that explicitly fail regex tests",
    )
    license: str | None = Field(
        default=None,
        description="The license for the resource",
    )
    version: str | None = Field(
        default=None,
        description="The version for the resource",
    )
    part_of: str | None = Field(
        default=None,
        description=(
            "An annotation between this prefix and a super-prefix. For example, "
            "``chembl.compound`` is a part of ``chembl``."
        ),
    )
    part_of_database: str | None = Field(default=None)
    provides: str | None = Field(
        default=None,
        description=(
            "An annotation between this prefix and a prefix for which it is redundant. "
            "For example, ``ctd.gene`` has been given a prefix by Identifiers.org, but it "
            "actually just reuses identifies from ``ncbigene``, so ``ctd.gene`` provides ``ncbigene``."
        ),
    )
    download_owl: str | None = Field(
        default=None,
        title="OWL Download URL",
        description=_dedent(
            """\
    The URL to download the resource as an ontology encoded in the OWL format.
    More information about this format can be found at https://www.w3.org/TR/owl2-syntax/.
    """
        ),
    )
    download_obo: str | None = Field(
        default=None,
        title="OBO Download URL",
        description=_dedent(
            """\
    The URL to download the resource as an ontology encoded in the OBO format.
    More information about this format can be found at https://owlcollab.github.io/oboformat/doc/obo-syntax.html.
    """
        ),
    )
    download_json: str | None = Field(
        default=None,
        title="OBO Graph JSON Download URL",
        description=_dedent(
            """
    The URL to download the resource as an ontology encoded in the OBO Graph JSON format.
    More information about this format can be found at https://github.com/geneontology/obographs.
    """
        ),
    )
    download_rdf: str | AnnotatedURL | None = Field(
        default=None,
        title="RDF Download URL",
        description=_dedent(
            """
    The URL to download the resource as an RDF file, in one of many formats.
    """
        ),
    )
    download_skos: str | AnnotatedURL | None = Field(
        default=None,
        title="SKOS RDF Download URL",
        description="The URL to download the resource as an SKOS RDF file.",
    )
    download_jskos: str | None = Field(
        default=None,
        title="JSKOS Download URL",
        description="The URL to download the resource as an JSKOS JSON file.",
    )
    banana: str | None = Field(
        default=None,
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
    banana_peel: str | None = Field(default=None, description="Delimiter used in banana")
    deprecated: bool | None = Field(
        default=None,
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
    mappings: dict[str, str] | None = Field(
        default=None,
        description=_dedent(
            """\
    A dictionary of metaprefixes (i.e., prefixes for registries) to prefixes in external registries.
    These also correspond to the registry-specific JSON fields in this model like ``miriam`` field.
    """
        ),
    )
    synonyms: list[str] | None = Field(
        default=None,
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
    keywords: list[str] | None = Field(
        default=None, description="A list of keywords for the resource"
    )
    domain: Domain | None = Field(
        default=None,
        examples=cast(list[str], typing.get_args(Domain)),
        description="A high-level semantic type of the entities in the semantic space.",
    )
    references: list[str] | None = Field(
        default=None,
        description="A list of URLs to also see, such as publications describing the resource",
    )
    publications: list[Publication] | None = Field(
        default=None,
        description="A list of URLs to also see, such as publications describing the resource",
    )
    appears_in: list[str] | None = Field(
        default=None,
        description="A list of prefixes that use this resource for xrefs, provenance, etc.",
    )
    depends_on: list[str] | None = Field(
        default=None,
        description="A list of prefixes that use this resource depends on, e.g., ontologies that import each other.",
    )

    namespace_in_lui: bool | None = Field(
        default=None,
        title="Namespace Embedded in Local Unique Identifier",
        description=_dedent(
            """\
    A flag denoting if the namespace is embedded in the LUI (if this is true and it is not accompanied by a banana,
    assume that the banana is the prefix in all caps plus a colon, as is standard in OBO). Currently this flag
    is only used to override identifiers.org in the case of ``gramene.growthstage``, ``oma.hog``, and ``vario``.
    """
        ),
    )
    no_own_terms: bool | None = Field(
        default=None,
        description=_dedent(
            """\
    A flag denoting if the resource mints its own identifiers. Omission or explicit marking as false means
    that the resource does have its own terms. This is most applicable to ontologies, specifically application
    ontologies, which only reuse terms from others. One example is ChIRO.
    """
        ),
    )
    #: A field for a free text comment.
    comment: str | None = Field(
        default=None,
        description="A field for a free text comment",
    )

    contributor: Author | None = Field(
        default=None,
        description=_dedent(
            """\
    The contributor of the prefix to the Bioregistry, including at a minimum their name and ORCiD and
    optional their email address and GitHub handle. All entries curated through the Bioregistry GitHub
    Workflow must contain this field.
    """
        ),
    )
    contributor_extras: list[Author] | None = Field(
        default=None,
        description="Additional contributors besides the original submitter.",
    )

    reviewer: Author | None = Field(
        default=None,
        description=_dedent(
            """\
    The reviewer of the prefix to the Bioregistry, including at a minimum their name and ORCiD and
    optional their email address and GitHub handle. All entries curated through the Bioregistry GitHub
    Workflow should contain this field pointing to the person who reviewed it on GitHub.
    """
        ),
    )
    reviewer_extras: list[Author] | None = Field(
        default=None,
        description="Additional reviewers of the prefix.",
    )
    proprietary: bool | None = Field(
        default=None,
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
    has_canonical: str | None = Field(
        default=None,
        description="If this shares an IRI with another entry, maps to which should be be considered as canonical",
    )
    preferred_prefix: str | None = Field(
        default=None,
        description=_dedent(
            """\
    An annotation of stylization of the prefix. This appears in OBO ontologies like
    FBbt as well as databases like NCBIGene. If it's not given, then assume that
    the normalized prefix used in the Bioregistry is canonical.
    """
        ),
    )
    mastodon: str | None = Field(default=None, description="The mastodon handle for the project")
    github_request_issue: int | None = Field(
        default=None, description="The GitHub issue for the new prefix request"
    )
    logo: str | None = Field(
        default=None, description="The URL of the logo for the project/resource"
    )

    #: External data from Identifiers.org's MIRIAM Database
    miriam: Mapping[str, Any] | None = None
    #: External data from the Name-to-Thing service
    n2t: Mapping[str, Any] | None = None
    #: External data from Prefix Commons
    prefixcommons: Mapping[str, Any] | None = None
    #: External data from Wikidata Properties
    wikidata: Mapping[str, Any] | None = None
    #: External data from Wikidata Entity
    wikidata_entity: Mapping[str, Any] | None = None
    #: External data from the Gene Ontology's custom registry
    go: Mapping[str, Any] | None = None
    #: External data from the Open Biomedical Ontologies (OBO) Foundry catalog
    obofoundry: Mapping[str, Any] | None = None
    #: External data from the BioPortal ontology repository
    bioportal: Mapping[str, Any] | None = None
    #: External data from the EcoPortal ontology repository
    ecoportal: Mapping[str, Any] | None = None
    #: External data from the AgroPortal ontology repository
    agroportal: Mapping[str, Any] | None = None
    #: External data from the CropOCT ontology curation tool
    cropoct: Mapping[str, Any] | None = None
    #: External data from the Ontology Lookup Service
    ols: Mapping[str, Any] | None = None
    #: External data from the AberOWL ontology repository
    aberowl: Mapping[str, Any] | None = None
    #: External data from the NCBI Genbank's custom registry
    ncbi: Mapping[str, Any] | None = None
    #: External data from UniProt's custom registry
    uniprot: Mapping[str, Any] | None = None
    #: External data from the BioLink Model's custom registry
    biolink: Mapping[str, Any] | None = None
    #: External data from the Cellosaurus custom registry
    cellosaurus: Mapping[str, Any] | None = None
    #: External data from the OntoBee
    ontobee: Mapping[str, Any] | None = None
    #: External data from ChemInf
    cheminf: Mapping[str, Any] | None = None
    #: External data from FAIRsharing
    fairsharing: Mapping[str, Any] | None = None
    #: External data from BioContext
    biocontext: Mapping[str, Any] | None = None
    #: External data from EDAM ontology
    edam: Mapping[str, Any] | None = None
    #: External data from re3data
    re3data: Mapping[str, Any] | None = None
    #: External data from hl7
    hl7: Mapping[str, Any] | None = None
    #: External data from bartoc
    bartoc: Mapping[str, Any] | None = Field(default=None, title="BARTOC")
    #: External data from RRID
    rrid: Mapping[str, Any] | None = Field(default=None, title="RRID")
    #: External data from LOV
    lov: Mapping[str, Any] | None = Field(default=None, title="LOV")
    #: External data from Zazuko
    zazuko: Mapping[str, Any] | None = Field(default=None)
    #: External data from TogoID
    togoid: Mapping[str, Any] | None = Field(default=None)
    #: External data from Integbio
    integbio: Mapping[str, Any] | None = Field(default=None)
    #: External data from PathGuide
    pathguide: Mapping[str, Any] | None = Field(default=None)
    #: External data from TIB Terminology Service
    tib: Mapping[str, Any] | None = Field(default=None)

    # Cached compiled pattern for identifiers
    _compiled_pattern: re.Pattern[str] | None = PrivateAttr(None)

    def get_external(self, metaprefix: str) -> Mapping[str, Any]:
        """Get an external registry."""
        return self.model_dump().get(metaprefix) or {}

    def get_mapped_prefix(self, metaprefix: str, use_obo_preferred: bool = True) -> str | None:
        """Get the prefix for the given external.

        :param metaprefix: The metaprefix for the external resource
        :param use_obo_preferred: Whether to use OBO preferred prefix

        :returns: The prefix in the external registry, if it could be mapped

        >>> from bioregistry import get_resource
        >>> get_resource("chebi").get_mapped_prefix("wikidata")
        'P683'
        >>> get_resource("chebi").get_mapped_prefix("obofoundry")
        'CHEBI'
        """
        if metaprefix == "obofoundry" and use_obo_preferred:
            obofoundry_dict = self.obofoundry or {}
            if "preferred_prefix" in obofoundry_dict:
                return cast(str, obofoundry_dict["preferred_prefix"])
            if "prefix" in obofoundry_dict:
                return cast(str, obofoundry_dict["prefix"]).upper()
            return None
        return self.get_mappings().get(metaprefix)

    # docstr-coverage:excused `overload`
    @overload
    def get_prefix_key(
        self,
        key: str,
        metaprefixes: str | Sequence[str],
        *,
        rv_type: type[X],
        provenance: Literal[True] = True,
    ) -> MetaprefixAnnotatedValue[X] | None: ...

    # docstr-coverage:excused `overload`
    @overload
    def get_prefix_key(
        self,
        key: str,
        metaprefixes: str | Sequence[str],
        *,
        rv_type: type[X],
        provenance: Literal[False] = False,
    ) -> X | None: ...

    def get_prefix_key(
        self,
        key: str,
        metaprefixes: str | Sequence[str],
        *,
        rv_type: type[X],
        provenance: bool = False,
    ) -> None | X | MetaprefixAnnotatedValue[X]:
        """Get a key enriched by the given external resources' data."""
        rv = self.model_dump().get(key)
        if rv is not None:
            if isinstance(rv, str):
                rv = rv.replace("\r\n", "\n")
            if provenance:
                return cast(
                    MetaprefixAnnotatedValue[X], MetaprefixAnnotatedValue(rv, "bioregistry")
                )
            return cast(X, rv)
        if isinstance(metaprefixes, str):
            metaprefixes = [metaprefixes]
        for metaprefix in metaprefixes:
            rv = self.get_external(metaprefix).get(key)
            if rv is not None:
                if isinstance(rv, str):
                    rv = rv.replace("\r\n", "\n")
                if provenance:
                    return cast(
                        MetaprefixAnnotatedValue[X], MetaprefixAnnotatedValue(rv, metaprefix)
                    )
                return cast(X, rv)
        return None

    # docstr-coverage:excused `overload`
    @overload
    def _get_prefix_key_str(
        self,
        key: str,
        metaprefixes: str | Sequence[str],
        *,
        provenance: Literal[False] = False,
    ) -> None | str: ...

    # docstr-coverage:excused `overload`
    @overload
    def _get_prefix_key_str(
        self, key: str, metaprefixes: str | Sequence[str], *, provenance: Literal[True] = True
    ) -> None | MetaprefixAnnotatedValue[str]: ...

    def _get_prefix_key_str(
        self, key: str, metaprefixes: str | Sequence[str], *, provenance: bool = False
    ) -> None | str | MetaprefixAnnotatedValue[str]:
        if provenance:
            return self.get_prefix_key(key, metaprefixes, rv_type=str, provenance=True)
        else:
            return self.get_prefix_key(key, metaprefixes, rv_type=str, provenance=False)

    # docstr-coverage:excused `overload`
    @overload
    def _get_prefix_key_bool(
        self,
        key: str,
        metaprefixes: str | Sequence[str],
        *,
        provenance: Literal[False] = False,
    ) -> None | bool: ...

    # docstr-coverage:excused `overload`
    @overload
    def _get_prefix_key_bool(
        self, key: str, metaprefixes: str | Sequence[str], *, provenance: Literal[True] = True
    ) -> None | MetaprefixAnnotatedValue[bool]: ...

    def _get_prefix_key_bool(
        self, key: str, metaprefixes: str | Sequence[str], *, provenance: bool = False
    ) -> None | bool | MetaprefixAnnotatedValue[bool]:
        if provenance:
            return self.get_prefix_key(key, metaprefixes, rv_type=bool, provenance=True)
        else:
            return self.get_prefix_key(key, metaprefixes, rv_type=bool, provenance=False)

    def get_default_uri(self, identifier: str) -> str | None:
        """Return the default URI for the identifier.

        :param identifier: The local identifier in the nomenclature represented by this
            resource

        :returns: The first-party provider URI for the local identifier, if one can be
            constructed

        >>> from bioregistry import get_resource
        >>> get_resource("chebi").get_default_uri("24867")
        'http://purl.obolibrary.org/obo/CHEBI_24867'
        """
        fmt = self.get_default_format()
        if fmt is None:
            return None
        return fmt.replace("$1", identifier)

    def get_rdf_uri(self, identifier: str) -> str | None:
        """Return the RDF URI for the identifier.

        :param identifier: The local identifier in the nomenclature represented by this
            resource

        :returns: The canonical RDF URI for the local identifier, if one can be
            constructed

        >>> from bioregistry import get_resource
        >>> get_resource("edam").get_rdf_uri("data_1153")
        'http://edamontology.org/data_1153'
        """
        fmt = self.get_rdf_uri_format()
        if fmt is None:
            return None
        return fmt.replace("$1", identifier)

    def __setitem__(self, key: str, value: Any) -> None:
        """Set an attribute on the resource."""
        setattr(self, key, value)

    def get_banana(self) -> str | None:
        """Get the optional redundant prefix to go before an identifier.

        A "banana" is an embedded prefix that isn't actually part of the identifier.
        Usually this corresponds to the prefix itself, with some specific stylization
        such as in the case of FBbt. The banana does NOT include a colon ":" at the end

        :returns: The banana, if the prefix is valid and has an associated banana.

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

        Banana is not inferred for OBO Foundry ontologies that were imported

        >>> get_resource("ncit").get_banana()
        None
        >>> get_resource("ncbitaxon").get_banana()
        None
        """
        if self.banana is not None:
            return self.banana
        if self.get_namespace_in_lui(provenance=False) is False:
            return None
        miriam_prefix = self.get_miriam_prefix()
        obo_preferred_prefix = self.get_obo_preferred_prefix()
        if miriam_prefix is not None and obo_preferred_prefix is not None:
            return obo_preferred_prefix
        return None

    def get_banana_peel(self) -> str:
        """Get the delimiter between the banana and the local unique identifier."""
        return ":" if self.banana_peel is None else self.banana_peel

    def get_default_format(self) -> str | None:
        """Get the default, first-party URI prefix.

        :returns: The first-party URI prefix string, if available.

        >>> from bioregistry import get_resource
        >>> get_resource("ncbitaxon").get_default_format()
        'http://purl.obolibrary.org/obo/NCBITaxon_$1'
        >>> get_resource("go").get_default_format()
        'http://purl.obolibrary.org/obo/GO_$1'
        """
        if self.uri_format is not None:
            return self.uri_format
        for metaprefix, key in URI_FORMAT_PATHS:
            rv = cast(str | None, self.get_external(metaprefix).get(key))
            if rv is not None and _allowed_uri_format(rv):
                return rv
        return None

    def get_synonyms(self) -> set[str]:
        """Get synonyms."""
        return set(self.synonyms or {})

    def get_preferred_prefix(self) -> str | None:
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

        Preferred prefix from the OBO Foundry overridden by the Bioregistry (see also
        https://github.com/OBOFoundry/OBOFoundry.github.io/issues/1559)

        >>> get_resource("dpo").get_preferred_prefix()
        'DPO'
        """
        if self.preferred_prefix is not None:
            return self.preferred_prefix
        obo_preferred_prefix = self.get_obo_preferred_prefix()
        if obo_preferred_prefix is not None:
            return obo_preferred_prefix
        return None

    def get_obo_preferred_prefix(self) -> str | None:
        """Get the OBO preferred prefix, if this resource is mapped to the OBO Foundry."""
        if self.obofoundry is None:
            return None
        # if explicitly annotated, use it. Otherwise, the capitalized version
        # of the OBO Foundry ID is the preferred prefix (e.g., for GO)
        return cast(
            str, self.obofoundry.get("preferred_prefix") or self.obofoundry["prefix"].upper()
        )

    def get_wikidata_entity(self) -> str | None:
        """Get the wikidata database mapping."""
        if self.mappings and "wikidata.entity" in self.mappings:
            return self.mappings["wikidata.entity"]
        if self.wikidata and "database" in self.wikidata:
            return cast(str, self.wikidata["database"])
        if self.bartoc and "wikidata_database" in self.bartoc:
            return cast(str, self.bartoc["wikidata_database"])
        return None

    def get_mappings(self) -> dict[str, str]:
        """Get the mappings to external registries, if available."""
        return self.mappings or {}

    # docstr-coverage:excused `overload`
    @overload
    def get_name(self, *, provenance: Literal[False] = ...) -> None | str: ...

    # docstr-coverage:excused `overload`
    @overload
    def get_name(
        self, *, provenance: Literal[True] = ...
    ) -> None | MetaprefixAnnotatedValue[str]: ...

    def get_name(self, *, provenance: bool = False) -> None | str | MetaprefixAnnotatedValue[str]:
        """Get the name for the given prefix, if it's available."""
        if provenance:
            return self._get_prefix_key_str("name", DEFAULT_METAPREFIX_PRIORITY, provenance=True)
        return self._get_prefix_key_str("name", DEFAULT_METAPREFIX_PRIORITY, provenance=False)

    def get_description(self, use_markdown: bool = False) -> str | None:
        """Get the description for the given prefix, if available."""
        if self.description and use_markdown:
            import markupsafe
            from markdown import markdown

            return markupsafe.Markup(markdown(self.description))
        metaprefixes: Sequence[str] = (
            "miriam",
            "n2t",
            "ols",
            "obofoundry",
            "wikidata",
            "fairsharing",
            "aberowl",
            "bioportal",
            "agroportal",
            "ecoportal",
            "cropoct",
            "cheminf",
            "edam",
            "prefixcommons",
            "bartoc",
            "lov",
            "re3data",
            "tib",
            "integbio",
            "cellosaurus",
        )
        rv = self._get_prefix_key_str("description", metaprefixes, provenance=False)
        if rv is not None:
            return rv.strip()
        return None

    def get_pattern(self) -> str | None:
        """Get the pattern for the given prefix, if it's available.

        :returns: The pattern for the prefix, if it is available, using the following
            order of preference:

            1. Custom
            2. MIRIAM
            3. Wikidata
            4. BARTOC
        """
        if self.pattern is not None:
            return self.pattern
        rv = self._get_prefix_key_str("pattern", ("miriam", "wikidata", "bartoc"))
        if rv is None:
            return None
        return _clean_pattern(rv)

    def get_pattern_re(self) -> typing.Pattern[str] | None:
        """Get the compiled pattern for the given prefix, if it's available."""
        if self._compiled_pattern:
            return self._compiled_pattern
        pattern = self.get_pattern()
        if pattern is None:
            return None
        self._compiled_pattern = re.compile(pattern)
        return self._compiled_pattern

    def get_pattern_with_banana(self, strict: bool = True) -> str | None:
        r"""Get the pattern for the prefix including a banana if available.

        .. warning::

            This function is meant to mediate backwards compatibility with legacy
            MIRIAM/Identifiers.org standards. New projects should **not** use redundant
            prefixes in their local unique identifiers.

        :param strict: If True (default), and a banana exists for the prefix, the banana
            is required in the pattern. If False, the pattern will match the banana if
            present but will also match the identifier without the banana.

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

    def get_pattern_re_with_banana(self, strict: bool = True) -> typing.Pattern[str] | None:
        """Get the compiled pattern for the prefix including a banana if available.

        .. warning::

            This function is meant to mediate backwards compatibility with legacy
            MIRIAM/Identifiers.org standards. New projects should **not** use redundant
            prefixes in their local unique identifiers.

        :param strict: If True (default), and a banana exists for the prefix, the banana
            is required in the pattern. If False, the pattern will match the banana if
            present but will also match the identifier without the banana.

        :returns: A compiled pattern for the prefix if available

        >>> import bioregistry as br
        >>> resource = br.get_resource("chebi")

        Strict match requires banana

        >>> resource.get_pattern_re_with_banana().match("1234")

        >>> resource.get_pattern_re_with_banana().match("CHEBI:1234")
        <re.Match object; span=(0, 10), match='CHEBI:1234'>

        Loose match does not require banana

        >>> resource.get_pattern_re_with_banana(strict=False).match("1234")
        <re.Match object; span=(0, 4), match='1234'>
        >>> resource.get_pattern_re_with_banana(strict=False).match("CHEBI:1234")
        <re.Match object; span=(0, 10), match='CHEBI:1234'>
        """
        p = self.get_pattern_with_banana(strict=strict)
        if p is None:
            return None
        return re.compile(p)

    # docstr-coverage:excused `overload`
    @overload
    def get_namespace_in_lui(
        self, *, provenance: Literal[True] = True
    ) -> MetaprefixAnnotatedValue[bool] | None: ...

    # docstr-coverage:excused `overload`
    @overload
    def get_namespace_in_lui(self, *, provenance: Literal[False] = False) -> bool | None: ...

    def get_namespace_in_lui(
        self, *, provenance: bool = False
    ) -> MetaprefixAnnotatedValue[bool] | bool | None:
        """Check if the namespace should appear in the LUI."""
        if self.namespace_in_lui is not None:
            return self.namespace_in_lui
        if miriam := self.get_external("miriam"):
            rv = miriam["extras"][MIRIAM_NAMESPACE_IN_LUI]
            if provenance:
                return MetaprefixAnnotatedValue[bool](value=rv, metaprefix="miriam")
            return cast(bool, rv)
        return False

    def get_homepage(self) -> str | None:
        """Return the homepage, if available."""
        return self._get_prefix_key_str("homepage", DEFAULT_METAPREFIX_PRIORITY)

    def get_domain(self) -> str | None:
        """Get the domain."""
        if self.domain:
            return self.domain
        # TODO map in OBO Foundry domain
        return None

    def get_keywords(self) -> list[str]:
        """Get keywords."""
        keywords = []
        if self.keywords:
            keywords.extend(self.keywords)
        for metaprefix in self.mappings or []:
            if kk := self.get_external(metaprefix).get("keywords"):
                keywords.extend(kk)
        if self.get_download_obo() or self.get_download_owl() or self.bioportal:
            keywords.append("ontology")
        return sorted(
            {
                keyword.lower().replace("’", "'")  # noqa:RUF001
                for keyword in keywords
                if keyword
            }
        )

    def get_repository(self) -> str | None:
        """Return the repository, if available."""
        if self.repository:
            return self.repository
        return self._get_prefix_key_str("repository", DEFAULT_METAPREFIX_PRIORITY)

    def get_contact(self) -> Attributable | None:
        """Get the contact, if available.

        :returns: A contact

        >>> from bioregistry import get_resource
        >>> get_resource("frapo").get_contact().email
        'silvio.peroni@unibo.it'
        """
        if self.contact is not None:
            return self.contact

        contacts = []
        for metaprefix in self.mappings or []:
            if contact := self.get_external(metaprefix).get("contact"):
                if contact.get("name"):
                    contacts.append(Attributable.model_validate(contact))
        if contacts:
            return max(contacts, key=lambda c: c.get_score())
        return None

    def get_contact_email(self) -> str | None:
        """Return the contact email, if available.

        :returns: The resource's contact email address, if it is available.

        >>> from bioregistry import get_resource
        >>> get_resource("bioregistry").get_contact_email()  # from bioregistry curation
        'cthoyt@gmail.com'
        >>> get_resource("chebi").get_contact_email()
        'amalik@ebi.ac.uk'
        >>> get_resource("frapo").get_contact_email()
        'silvio.peroni@unibo.it'
        """
        if contact := self.get_contact():
            return contact.email
        return None

    def get_contact_name(self) -> str | None:
        """Return the contact name, if available.

        :returns: The resource's contact name, if it is available.

        >>> from bioregistry import get_resource
        >>> get_resource("bioregistry").get_contact_name()  # from bioregistry curation
        'Charles Tapley Hoyt'
        >>> get_resource("chebi").get_contact_name()
        'Adnan Malik'
        >>> get_resource("frapo").get_contact_name()
        'Silvio Peroni'
        """
        if contact := self.get_contact():
            return contact.name
        return None

    def get_contact_github(self) -> str | None:
        """Return the contact GitHub handle, if available.

        :returns: The resource's contact GitHub handle, if it is available.

        >>> from bioregistry import get_resource
        >>> get_resource("bioregistry").get_contact_github()  # from bioregistry curation
        'cthoyt'
        >>> get_resource("agro").get_contact_github()  # from OBO Foundry
        'marieALaporte'
        """
        if contact := self.get_contact():
            if contact.github:
                return contact.github
            elif contact.orcid and contact.orcid in ORCID_TO_GITHUB:
                return ORCID_TO_GITHUB[contact.orcid]
        return None

    def get_contact_orcid(self) -> str | None:
        """Return the contact ORCiD, if available.

        :returns: The resource's contact ORCiD, if it is available.

        >>> from bioregistry import get_resource
        >>> get_resource("bioregistry").get_contact_orcid()  # from bioregistry curation
        '0000-0003-4423-4370'
        >>> get_resource("aero").get_contact_orcid()
        '0000-0002-9551-6370'
        >>> get_resource("frapo").get_contact_orcid()
        '0000-0003-0530-4305'
        """
        if self.contact and self.contact.orcid:
            return self.contact.orcid
        if self.obofoundry and "contact.orcid" in self.obofoundry:
            return cast(str, self.obofoundry["contact.orcid"])
        if self.fairsharing:
            rv = self.fairsharing.get("contact", {}).get("orcid")
            if rv:
                return cast(str, rv)
        return None

    # docstr-coverage:excused `overload`
    @overload
    def get_example(self, *, strict: Literal[False] = False) -> str | None: ...

    # docstr-coverage:excused `overload`
    @overload
    def get_example(self, *, strict: Literal[True] = True) -> str: ...

    def get_example(self, *, strict: bool = False) -> str | None:
        """Get an example identifier, if it's available."""
        if self.example is not None:
            return self.example
        for metaprefix in DEFAULT_METAPREFIX_PRIORITY:
            if examples := self.get_external(metaprefix).get("examples", []):
                return cast(str, examples[0])
        if strict:
            raise ValueError
        return None

    def get_examples(self) -> list[str]:
        """Get a list of examples."""
        rv = []
        example = self.get_example()
        if example:
            rv.append(example)
        rv.extend(self.get_example_extras())
        return rv

    def get_example_extras(self) -> list[str]:
        """Aggregate manually curated examples with provider-specific examples."""
        rv = set(self.example_extras or [])
        if self.providers:
            for provider in self.providers:
                if provider.example:
                    rv.add(provider.example)
        return sorted(rv)

    def get_example_curie(self, use_preferred: bool = False) -> str | None:
        """Get an example CURIE, if an example identifier is available.

        :param use_preferred: Should the preferred prefix be used instead of the
            Bioregistry prefix (if it exists)?

        :returns: An example CURIE for this resource
        """
        example = self.get_example()
        if example is None:
            return None
        return self.get_curie(example, use_preferred=use_preferred)

    def get_example_iri(self) -> str | None:
        """Get an example IRI."""
        example = self.get_example()
        if example is None:
            return None
        return self.get_default_uri(example)

    def is_deprecated(self) -> bool:
        """Return if the given prefix corresponds to a deprecated resource.

        :returns: If the prefix has been explicitly marked as deprecated either by the
            Bioregistry, OBO Foundry, OLS, or MIRIAM. If no marks are present, assumed
            not to be deprecated.

        >>> from bioregistry import get_resource
        >>> assert get_resource("imr").is_deprecated()  # marked by OBO
        >>> assert get_resource("iro").is_deprecated()  # marked by Bioregistry
        >>> assert get_resource("miriam.collection").is_deprecated()  # marked by MIRIAM
        """
        if self.deprecated is not None:
            return self.deprecated
        for key in DEFAULT_METAPREFIX_PRIORITY:
            if self.get_external(key).get("status") in {"deprecated", "inactive"}:
                return True
        return False

    def get_publications(self) -> list[Publication]:
        """Get a list of publications."""
        publications = self.publications or []
        for metaprefix in self.mappings or []:
            for publication in self.get_external(metaprefix).get("publications", []):
                publication = Publication.model_validate(publication)
                if publication.pubmed or publication.doi or publication.pmc:
                    publications.append(publication)
        for provider in self.providers or []:
            publications.extend(provider.publications or [])
        return deduplicate_publications(publications)

    def get_mastodon(self) -> str | None:
        """Get the Mastodon handle for the resource.

        :returns: The Mastodon handle. Note that this does **not** include a leading
            ``@``

        >>> from bioregistry import get_resource
        >>> get_resource("go").get_mastodon()
        'go@genomic.social'
        """
        if self.mastodon:
            return self.mastodon
        return None

    def get_mastodon_url(self) -> str | None:
        """Get the Mastodon URL for the resource.

        :returns: The URL link for the mastodon account, if available

        >>> from bioregistry import get_resource
        >>> get_resource("go").get_mastodon_url()
        'https://genomic.social/@go'
        """
        mastodon = self.get_mastodon()
        if mastodon is None:
            return None
        username, server = mastodon.split("@")
        return f"https://{server}/@{username}"

    def get_twitter(self) -> str | None:
        """Get the Twitter handle for the resource."""
        raise NotImplementedError("twitter is no longer tracked")

    def get_logo(self) -> str | None:
        """Get the logo for the resource."""
        if self.logo:
            return self.logo
        if self.obofoundry and "logo" in self.obofoundry:
            return cast(str, self.obofoundry["logo"])
        if self.fairsharing and "logo" in self.fairsharing:
            return cast(str, self.fairsharing["logo"])
        return None

    def get_mailing_list(self) -> str | None:
        """Get the group email."""
        if self.contact_group_email:
            return str(self.contact_group_email)
        return None

    def get_obofoundry_prefix(self) -> str | None:
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
        return self.get_mapped_prefix("obofoundry", use_obo_preferred=True)

    def get_obofoundry_uri_prefix(self) -> str | None:
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

    def get_bioregistry_uri_format(self) -> str | None:
        """Get the Bioregisry URI format string for this entry.

        :returns: A Bioregistry URI, if this can be resolved.

        >>> from bioregistry import get_resource
        >>> get_resource("go").get_bioregistry_uri_format()
        'https://bioregistry.io/go:$1'
        """
        if not self.get_default_format():
            return None
        return f"https://bioregistry.io/{self.prefix}:$1"

    def get_obofoundry_uri_format(self) -> str | None:
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

    def _get_external_uri_format(self, metaprefix: str) -> str | None:
        return self.get_external(metaprefix).get(URI_FORMAT_KEY)

    def get_biocontext_uri_format(self) -> str | None:
        """Get the BioContext URI format string for this entry, if available.

        :returns: The BioContext URI format string, if available.

        >>> from bioregistry import get_resource
        >>> get_resource("hgmd").get_biocontext_uri_format()
        'http://www.hgmd.cf.ac.uk/ac/gene.php?gene=$1'
        """
        return self._get_external_uri_format("biocontext")

    def get_bartoc_uri_format(self) -> str | None:
        """Get the BARTOC URI format string for this entry, if available.

        :returns: The BARTOC URI format string, if available.

        >>> from bioregistry import get_resource
        >>> get_resource("ddc").get_bartoc_uri_format()
        'http://dewey.info/class/$1/e23/'
        """
        return self._get_external_uri_format("bartoc")

    def get_prefixcommons_prefix(self) -> str | None:
        """Get the Prefix Commons prefix."""
        return self.get_mapped_prefix("prefixcommons")

    def get_prefixcommons_uri_format(self) -> str | None:
        """Get the Prefix Commons URI format string for this entry, if available.

        :returns: The Prefix Commons URI format string, if available.

        >>> from bioregistry import get_resource
        >>> get_resource("antweb").get_prefixcommons_uri_format()
        'http://www.antweb.org/specimen.do?name=$1'
        """
        return self._get_external_uri_format("prefixcommons")

    def get_identifiers_org_prefix(self) -> str | None:
        """Get the MIRIAM/Identifiers.org prefix, if available.

        :returns: The Identifiers.org/MIRIAM prefix corresponding to the prefix, if
            mappable.

        >>> from bioregistry import get_resource
        >>> get_resource("chebi").get_identifiers_org_prefix()
        'chebi'
        >>> get_resource("ncbitaxon").get_identifiers_org_prefix()
        'taxonomy'
        >>> assert get_resource("bioregistry").get_identifiers_org_prefix() is None
        """
        return self.get_mapped_prefix("miriam")

    def get_miriam_prefix(self) -> str | None:
        """Get the MIRIAM/Identifiers.org prefix, if available."""
        return self.get_identifiers_org_prefix()

    def get_miriam_uri_prefix(
        self,
        legacy_delimiter: bool = False,
        legacy_protocol: bool = False,
        legacy_banana: bool = False,
    ) -> str | None:
        """Get the Identifiers.org URI prefix for this entry, if possible.

        :param legacy_protocol: If true, uses HTTP
        :param legacy_delimiter: If true, uses a slash delimiter for CURIEs instead of
            colon
        :param legacy_banana: If true, uses a slash delimiter for CURIEs and a redundant
            namespace in prefix

        :returns: The Identifiers.org/MIRIAM URI prefix, if available.

        >>> from bioregistry import get_resource
        >>> get_resource("ncbitaxon").get_miriam_uri_prefix()
        'https://identifiers.org/taxonomy:'
        >>> get_resource("go").get_miriam_uri_prefix()
        'https://identifiers.org/GO:'
        >>> get_resource("doid").get_miriam_uri_prefix(legacy_banana=True)
        'https://identifiers.org/doid/DOID:'
        >>> get_resource("vario").get_miriam_uri_prefix(legacy_banana=True)
        'https://identifiers.org/vario/VariO:'
        >>> get_resource("cellosaurus").get_miriam_uri_prefix(legacy_banana=True)
        'https://identifiers.org/cellosaurus/CVCL_'
        >>> get_resource("doid").get_miriam_uri_prefix(legacy_delimiter=True)
        'https://identifiers.org/DOID/'
        >>> assert get_resource("sty").get_miriam_uri_prefix() is None
        """
        miriam_prefix = self.get_identifiers_org_prefix()
        if miriam_prefix is None:
            return None
        protocol = "http" if legacy_protocol else "https"
        if legacy_banana and self.get_banana():
            return f"{protocol}://identifiers.org/{miriam_prefix}/{self.get_banana()}{self.get_banana_peel()}"
        if self.get_namespace_in_lui():
            # not exact solution, some less common ones don't use capitalization
            # align with the banana solution
            miriam_prefix = miriam_prefix.upper()
        delimiter = "/" if legacy_delimiter else ":"
        return f"{protocol}://identifiers.org/{miriam_prefix}{delimiter}"

    def get_miriam_uri_format(
        self,
        legacy_delimiter: bool = False,
        legacy_protocol: bool = False,
        legacy_banana: bool = False,
    ) -> str | None:
        """Get the Identifiers.org URI format string for this entry, if possible.

        :param legacy_protocol: If true, uses HTTP
        :param legacy_delimiter: If true, uses a slash delimiter for CURIEs instead of
            colon
        :param legacy_banana: If true, uses a slash delimiter for CURIEs and a redundant
            namespace in prefix

        :returns: The Identifiers.org/MIRIAM URL format string, if available.

        >>> from bioregistry import get_resource
        >>> get_resource("ncbitaxon").get_miriam_uri_format()
        'https://identifiers.org/taxonomy:$1'
        >>> get_resource("go").get_miriam_uri_format()
        'https://identifiers.org/GO:$1'
        >>> assert get_resource("sty").get_miriam_uri_format() is None
        """
        miriam_url_prefix = self.get_miriam_uri_prefix(
            legacy_delimiter=legacy_delimiter,
            legacy_protocol=legacy_protocol,
            legacy_banana=legacy_banana,
        )
        if miriam_url_prefix is None:
            return None
        return f"{miriam_url_prefix}$1"

    def get_legacy_miriam_uri_format(self) -> str | None:
        """Get the legacy Identifiers.org URI format string for this entry, if possible."""
        return self.get_miriam_uri_format(legacy_protocol=True, legacy_delimiter=True)

    def get_legacy_alt_miriam_uri_format(self) -> str | None:
        """Get the legacy Identifiers.org URI format string for this entry, if possible."""
        return self.get_miriam_uri_format(
            legacy_protocol=True, legacy_delimiter=True, legacy_banana=True
        )

    def get_nt2_uri_prefix(self, legacy_protocol: bool = False) -> str | None:
        """Get the Name-to-Thing URI prefix for this entry, if possible."""
        n2t_prefix = self.get_mapped_prefix("n2t")
        if n2t_prefix is None:
            return None
        protocol = "http" if legacy_protocol else "https"
        return f"{protocol}://n2t.net/{n2t_prefix}:"

    def get_n2t_uri_format(self, legacy_protocol: bool = False) -> str | None:
        """Get the Name-to-Thing URI format string, if available."""
        n2t_uri_prefix = self.get_nt2_uri_prefix(legacy_protocol=legacy_protocol)
        if n2t_uri_prefix is None:
            return None
        return f"{n2t_uri_prefix}$1"

    def get_scholia_prefix(self) -> str | None:
        """Get the Scholia prefix, if available."""
        return self.get_mapped_prefix("scholia")

    def get_ols_prefix(self) -> str | None:
        """Get the OLS prefix if available."""
        return self.get_mapped_prefix("ols")

    def get_ols_uri_prefix(self) -> str | None:
        """Get the OLS URI prefix for this entry, if possible.

        :returns: The OLS URI prefix, if available.

        .. warning::

            This doesn't have a normal form, so it only works for OBO Foundry at the
            moment.

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

    def get_ols_uri_format(self) -> str | None:
        """Get the OLS URI format string for this entry, if possible.

        :returns: The OLS format string, if available.

        .. warning::

            This doesn't have a normal form, so it only works for OBO Foundry at the
            moment.

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

    def get_rrid_uri_format(self) -> str | None:
        """Get the RRID URI format.

        :returns: The RRID format string, if available.

        >>> from bioregistry import get_resource
        >>> get_resource("antibodyregistry").get_rrid_uri_format()  # standard
        'https://scicrunch.org/resolver/RRID:AB_$1'
        >>> assert get_resource("go").get_rrid_uri_format() is None
        """
        if not self.rrid:
            return None
        prefix = self.rrid["prefix"]
        return f"https://scicrunch.org/resolver/RRID:{prefix}_$1"

    def get_rdf_uri_format(self) -> str | None:
        """Get the URI format string for the given prefix for RDF usages."""
        if self.rdf_uri_format:
            return self.rdf_uri_format
        if self.obofoundry:
            return self.get_obofoundry_uri_format()
        if self.wikidata and "uri_format_rdf" in self.wikidata:
            return cast(str, self.wikidata["uri_format_rdf"])
        # TODO also pull from Prefix Commons
        return None

    def get_rdf_uri_prefix(self) -> str | None:
        """Get the URI prefix for the prefix for RDF usages."""
        rdf_uri_format = self.get_rdf_uri_format()
        return self._clip_uri_format(rdf_uri_format)

    URI_FORMATTERS: ClassVar[Mapping[str, Callable[[Resource], str | None]]] = {
        "default": get_default_format,
        "rdf": get_rdf_uri_format,
        "bioregistry": get_bioregistry_uri_format,
        "obofoundry": get_obofoundry_uri_format,
        "prefixcommons": get_prefixcommons_uri_format,
        "biocontext": get_biocontext_uri_format,
        "miriam": get_miriam_uri_format,
        "miriam.legacy": get_legacy_miriam_uri_format,
        "miriam.legacy_banana": get_legacy_alt_miriam_uri_format,
        "n2t": get_n2t_uri_format,
        "ols": get_ols_uri_format,
        "rrid": get_rrid_uri_format,
    }

    #: The point of this priority order is to figure out what URI format string
    #: to give back. The "default" means it's going to go into the metaregistry
    #: and try and find a real URI, not a re-directed one. If it can't manage that,
    #: try and get an OBO foundry redirect (though note this is only applicable to
    #: a small number of prefixes corresponding to ontologies). Finally, if this
    #: doesn't work, give a Bioregistry URI
    DEFAULT_URI_FORMATTER_PRIORITY: ClassVar[Sequence[str]] = (
        "default",
        "obofoundry",
        "bioregistry",
    )

    def get_priority_prefix(self, priority: None | str | Sequence[str] = None) -> str:
        """Get a prioritized prefix.

        :param priority: A metaprefix or list of metaprefixes used to choose a
            prioritized prefix. Some special values that are not themselves metaprefixes
            are allowed from the following list:

            - "default": corresponds to the bioregistry prefix
            - "bioregistry.upper": an uppercase transform of the canonical bioregistry
              prefix
            - "preferred": a preferred prefix, typically includes stylization in
              capitalization
            - "obofoundry.preferred": the preferred prefix annotated in OBO Foundry

        :returns: The prioritized prefix for this record
        """
        if priority is None:
            return self.prefix
        if isinstance(priority, str):
            priority = [priority]
        mappings = self.get_mappings()
        _default = {"default", "bioregistry"}
        for metaprefix in priority:
            if metaprefix in _default:
                return self.prefix
            if metaprefix == "bioregistry.upper":
                return self.prefix.upper()
            if metaprefix == "preferred":
                preferred_prefix = self.get_preferred_prefix()
                if preferred_prefix:
                    return preferred_prefix
            if metaprefix == "obofoundry.preferred":
                preferred_prefix = self.get_obo_preferred_prefix()
                if preferred_prefix:
                    return preferred_prefix
            if metaprefix in mappings:
                return mappings[metaprefix]
        return self.prefix

    def _iterate_uri_formats(self, priority: Sequence[str] | None = None) -> Iterable[str]:
        for metaprefix in priority or self.DEFAULT_URI_FORMATTER_PRIORITY:
            formatter = self.URI_FORMATTERS.get(metaprefix)
            if formatter is None:
                logger.warning("could not get formatter for %s", metaprefix)
                continue
            uri_format = formatter(self)
            if uri_format is None:
                continue
            yield uri_format

    def get_uri_format(self, priority: Sequence[str] | None = None) -> str | None:
        """Get the URI format string for the given prefix, if it's available.

        :param priority: The priority order of metaresources to use for format URI
            lookup. The default is:

            1. Manually curated URI Format in the Bioregistry
            2. Default first party (e.g., MIRIAM, BioContext, Prefix Commons, Wikidata)
            3. OBO Foundry
            4. MIRIAM/Identifiers.org (i.e., make a URI like
               https://identifiers.org/<prefix>:<identifier>)
            5. N2T (i.e., make a URI like https://n2t.org/<prefix>:<identifier>)
            6. OLS

        :returns: The best URI format string, where the ``$1`` should be replaced by a
            local unique identifier. ``$1`` could potentially appear multiple times.

        >>> from bioregistry import get_resource
        >>> get_resource("chebi").get_uri_format()
        'http://purl.obolibrary.org/obo/CHEBI_$1'

        If you want to specify a different priority order, you can do so with the
        ``priority`` keyword. This is of particular interest to ontologists and semantic
        web people who might want to use ``purl.obolibrary.org`` URL prefixes over the
        URL prefixes corresponding to the first-party providers for each resource (e.g.,
        the ChEBI example above). Do so like:

        >>> from bioregistry import get_resource
        >>> priority = ["obofoundry", "bioregistry", "biocontext", "miriam", "ols"]
        >>> get_resource("chebi").get_uri_format(priority=priority)
        'http://purl.obolibrary.org/obo/CHEBI_$1'
        """
        for uri_format in self._iterate_uri_formats(priority):
            return uri_format
        return None

    # docstr-coverage:excused `overload`
    @overload
    def get_uri_prefix(
        self, priority: Sequence[str] | None = None, *, strict: Literal[False] = ...
    ) -> str | None: ...

    # docstr-coverage:excused `overload`
    @overload
    def get_uri_prefix(
        self, priority: Sequence[str] | None = None, *, strict: Literal[True] = ...
    ) -> str: ...

    def get_uri_prefix(
        self, priority: Sequence[str] | None = None, *, strict: bool = False
    ) -> str | None:
        """Get a well-formed URI prefix, if available.

        :param priority: The prioirty order for :func:`get_format`.

        :returns: The URI prefix. Similar to what's returned by :func:`get_uri_format`,
            but it MUST have only one ``$1`` and end with ``$1`` to use the function.

        >>> import bioregistry
        >>> bioregistry.get_uri_prefix("chebi")
        'http://purl.obolibrary.org/obo/CHEBI_'
        """
        for uri_format in self._iterate_uri_formats(priority):
            uri_prefix = self._clip_uri_format(uri_format)
            if uri_prefix is not None:
                return uri_prefix
        if strict:
            raise ValueError
        return None

    def _clip_uri_format(self, uri_format: str | None) -> str | None:
        if uri_format is None or uri_format == "None":
            return None
        if uri_format != uri_format.rstrip():
            logging.debug("[%s] formatter has whitespace on right: %s", self.prefix, uri_format)
            uri_format = uri_format.rstrip()
        count = uri_format.count("$1")
        if 0 == count:
            logging.debug("[%s] formatter missing $1: %s", self.prefix, uri_format)
            return None
        if uri_format.count("$1") != 1:
            logging.debug("[%s] formatter has multiple $1: %s", self.prefix, uri_format)
            return None
        if not uri_format.endswith("$1"):
            logging.debug("[%s] formatter does not end with $1: %s", self.prefix, uri_format)
            return None
        return uri_format[: -len("$1")]

    def get_uri_prefixes(self, *, enforce_w3c: bool = False) -> set[str]:
        """Get the set of all URI prefixes.

        :param enforce_w3c: When generating URI prefixes from prefix synonyms, should
            synonyms that aren't W3C-compliant be filtered out?

        :returns: A set of URI prefixes.
        """
        uri_prefixes = (
            self._clip_uri_format(uri_format)
            for uri_format in self.get_uri_formats(enforce_w3c=enforce_w3c)
        )
        return {uri_prefix for uri_prefix in uri_prefixes if uri_prefix is not None}

    def get_uri_formats(self, *, enforce_w3c: bool = False) -> set[str]:
        """Get the set of all URI format strings.

        :param enforce_w3c: When generating URI prefixes from prefix synonyms, should
            synonyms that aren't W3C-compliant be filtered out?

        :returns: A set of URI format strings, containing ``$1`` where a local unique
            identifier should be formatted in.
        """
        uri_formats = itt.chain.from_iterable(
            _yield_protocol_variations(uri_format)
            for uri_format in self._iter_uri_formats(enforce_w3c=enforce_w3c)
        )
        return set(uri_formats)

    def _iter_uri_formats(self, *, enforce_w3c: bool = False) -> Iterable[str]:
        if self.uri_format:
            yield self.uri_format
        yield f"https://bioregistry.io/{self.prefix}:$1"
        preferred_prefix = self.get_preferred_prefix()
        if preferred_prefix:
            yield f"https://bioregistry.io/{preferred_prefix}:$1"
        for synonym in self.get_synonyms():
            if not enforce_w3c or NCNAME_RE.fullmatch(synonym):
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
        rdf_uri_format = self.get_rdf_uri_format()
        if rdf_uri_format:
            yield rdf_uri_format

    def get_extra_providers(self, *, filter_known_inactive: bool = False) -> list[Provider]:
        """Get a list of all extra providers."""
        rv = []
        providers = self.providers or []
        provider_codes = {provider.code for provider in providers}
        provider_uris = {provider.uri_format for provider in providers}
        rv.extend(providers)

        for metaprefix in DEFAULT_METAPREFIX_PRIORITY:
            for provider_raw in self.get_external(metaprefix).get("providers") or []:
                provider = Provider.model_validate(provider_raw)
                if provider.code in provider_codes or provider.uri_format in provider_uris:
                    # this means we've done an explicit override in the Bioregistry curated data
                    continue
                rv.append(provider)

        rv = sorted(rv, key=attrgetter("code"))
        if filter_known_inactive:
            rv = [v for v in rv if not v.is_known_inactive()]
        return rv

    def get_curie(self, identifier: str, use_preferred: bool = False) -> str:
        """Get a CURIE for a local unique identifier in this resource's semantic space.

        :param identifier: A local unique identifier in this resource's semantic space
        :param use_preferred: Should preferred prefixes be used? Set this to true if
            you're in the OBO context.

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

        :returns: A normalized identifier, possibly with banana/redundant prefix removed

        Examples with explicitly annotated bananas

        >>> from bioregistry import get_resource
        >>> get_resource("vario").standardize_identifier("0376")
        '0376'
        >>> get_resource("vario").standardize_identifier("VariO:0376")
        '0376'
        >>> get_resource("swisslipid").standardize_identifier("000000001")
        '000000001'
        >>> get_resource("swisslipid").standardize_identifier("SLM:000000001")
        '000000001'

        Examples with bananas from OBO

        >>> get_resource("fbbt").standardize_identifier("00007294")
        '00007294'
        >>> get_resource("chebi").standardize_identifier("1234")
        '1234'
        >>> get_resource("chebi").standardize_identifier("CHEBI:1234")
        '1234'
        >>> get_resource("chebi").standardize_identifier("CHEBI_1234")
        '1234'

        Examples from OBO Foundry that should not have a redundant prefix added

        >>> get_resource("ncit").standardize_identifier("C73192")
        'C73192'
        >>> get_resource("ncbitaxon").standardize_identifier("9606")
        '9606'

        Standard

        >>> get_resource("pdb").standardize_identifier("00000020")
        '00000020'
        """
        icf = identifier.casefold()
        banana = self.get_banana()
        peels = [self.get_banana_peel(), "_"]
        for peel in peels:
            prebanana = f"{banana}{peel}".casefold()
            if banana and icf.startswith(prebanana):
                return identifier[len(prebanana) :]
            elif icf.startswith(f"{self.prefix.casefold()}{peel}"):
                return identifier[len(self.prefix) + len(peel) :]
        return identifier

    def get_miriam_curie(self, identifier: str) -> str | None:
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

    def miriam_standardize_identifier(self, identifier: str) -> str | None:
        """Normalize the identifier for legacy usage with MIRIAM using the appropriate banana.

        :param identifier: The identifier in the CURIE

        :returns: A normalize identifier, possibly with banana/redundant prefix added

        Because identifiers.org used to have URIs in the form of
        https://identifiers.org/<prefix>/<prefix>:<identifier> for entries annotated
        with ``namespaceEmbeddedInLui`` as ``true``

        Examples with explicitly annotated bananas

        >>> from bioregistry import get_resource
        >>> get_resource("vario").miriam_standardize_identifier("0376")
        'VariO:0376'
        >>> get_resource("vario").miriam_standardize_identifier("VariO:0376")
        'VariO:0376'

        Examples with bananas from OBO

        >>> get_resource("go").miriam_standardize_identifier("0000001")
        'GO:0000001'
        >>> get_resource("go").miriam_standardize_identifier("GO:0000001")
        'GO:0000001'

        Examples from OBO Foundry

        >>> get_resource("chebi").miriam_standardize_identifier("1234")
        'CHEBI:1234'
        >>> get_resource("chebi").miriam_standardize_identifier("CHEBI:1234")
        'CHEBI:1234'

        Examples from OBO Foundry that should not have a redundant prefix added

        >>> get_resource("ncit").miriam_standardize_identifier("C73192")
        'C73192'
        >>> get_resource("ncbitaxon").miriam_standardize_identifier("9606")
        '9606'

        Standard

        >>> get_resource("pdb").miriam_standardize_identifier("00000020")
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

    def get_download_obo(self) -> str | None:
        """Get the download link for the latest OBO file.

        :returns: A URL for an OBO text file download, if exists.

        Get an ontology download link annotated directly in the Bioregistry:

        >>> from bioregistry import get_resource
        >>> get_resource("caloha").get_download_obo()
        'https://raw.githubusercontent.com/calipho-sib/controlled-vocabulary/master/caloha.obo'

        Get an ontology download link from the OBO Foundry:

        >>> get_resource("bfo").get_download_obo()
        'http://purl.obolibrary.org/obo/bfo.obo'

        Get ontology download link from OLS where OWL isn't available

        >>> get_resource("hpath").get_download_obo()
        'https://raw.githubusercontent.com/Novartis/hpath/master/src/hpath.obo'

        Get ontology download link in AberOWL but not OBO Foundry (note this might
        change over time so the exact value isn't used in the doctest):

        >>> url = get_resource("dermo").get_download_obo()
        >>> assert url is not None and url.startswith("http://aber-owl.net/media/ontologies/DERMO")
        """
        if self.download_obo:
            return self.download_obo
        return (
            self._get_download("obofoundry", "obo")
            or self._get_download("ols", "obo")
            or self._get_download("aberowl", "obo")
        )

    def get_download_obograph(self) -> str | None:
        """Get the download link for the latest OBOGraph JSON file."""
        if self.download_json:
            return self.download_json
        return self._get_download("obofoundry", "obograph_json")

    # docstr-coverage:excused `overload`
    @overload
    def get_download_rdf(self, *, get_format: Literal[True] = ...) -> str | AnnotatedURL | None: ...

    # docstr-coverage:excused `overload`
    @overload
    def get_download_rdf(self, *, get_format: Literal[False] = ...) -> str | None: ...

    def get_download_rdf(self, *, get_format: bool = False) -> str | AnnotatedURL | None:
        """Get the download link for the latest RDF file."""
        if self.download_rdf is not None:
            if isinstance(self.download_rdf, AnnotatedURL) and not get_format:
                return self.download_rdf.url
            else:
                return self.download_rdf
        return self._get_download("ols", "rdf")

    # docstr-coverage:excused `overload`
    @overload
    def get_download_skos(
        self, *, get_format: Literal[True] = ...
    ) -> str | AnnotatedURL | None: ...

    # docstr-coverage:excused `overload`
    @overload
    def get_download_skos(self, *, get_format: Literal[False] = ...) -> str | None: ...

    def get_download_skos(self, *, get_format: bool = False) -> str | AnnotatedURL | None:
        """Get the download link for the latest SKOS RDF file."""
        if self.download_skos is not None:
            if isinstance(self.download_skos, AnnotatedURL) and not get_format:
                return self.download_skos.url
            else:
                return self.download_skos
        return None

    def get_download_jskos(self) -> str | None:
        """Get the download link for the latest JSKOS JSON file."""
        return self.download_jskos

    def get_download_owl(self) -> str | None:
        """Get the download link for the latest OWL file.

        :returns: A URL for an OWL file download, if exists.

        Get an ontology download link annotated directly in the Bioregistry:

        >>> from bioregistry import get_resource
        >>> get_resource("orphanet.ordo").get_download_owl()
        'http://www.orphadata.org/data/ORDO/ordo_orphanet.owl'

        Get an ontology download link from the OBO Foundry:

        >>> get_resource("mod").get_download_owl()
        'http://purl.obolibrary.org/obo/mod.owl'

        Get ontology download link in AberOWL but not OBO Foundry (note this might
        change over time so the exact value isn't used in the doctest):

        >>> url = get_resource("birnlex").get_download_owl()
        >>> assert url is not None and url.startswith(
        ...     "http://aber-owl.net/media/ontologies/BIRNLEX/"
        ... )

        """
        if self.download_owl:
            return self.download_owl
        return (
            self._get_download("obofoundry", "owl")
            or self.get_external("ols").get("version.iri")
            or self._get_download("ols", "owl")
            or self._get_download("cropoct", "owl")
            or self._get_download("aberowl", "owl")
        )

    def _get_download(self, metaprefix: str, artifact_type: str) -> str | None:
        for artifact in self.get_external(metaprefix).get("artifacts", []):
            if artifact["type"] == artifact_type:
                return cast(str, artifact["url"])
        return None

    def has_download(self) -> bool:
        """Check if this resource can be downloaded."""
        return any(self._downloads())

    def _downloads(self) -> list[str | None]:
        return [
            self.get_download_obo(),
            self.get_download_owl(),
            self.get_download_obograph(),
            self.get_download_rdf(get_format=False),
        ]

    def get_download(self) -> str | None:
        """Get a download link."""
        for url in self._downloads():
            if url is not None:
                return url
        return None

    def get_license(self) -> str | None:
        """Get the license for the resource."""
        if self.license:
            return self.license
        for metaprefix in DEFAULT_METAPREFIX_PRIORITY:
            match self.get_external(metaprefix).get("license"):
                case str() as license_str:
                    if license_value := standardize_license(license_str):
                        return license_value
                case dict() as license_dict:
                    if "spdx" in license_dict:
                        return cast(str, license_dict["spdx"])
                    if "name" in license_dict and (
                        license_value := standardize_license(license_dict["name"])
                    ):
                        return license_value
        return None

    def get_license_url(self) -> str | None:
        """Get a license URL."""
        spdx_id = self.get_license()
        if spdx_id is None:
            return None
        return f"{BIOREGISTRY_REMOTE_URL}/spdx:{spdx_id}"

    def get_version(self) -> str | None:
        """Get the version for the resource."""
        if self.version:
            return self.version
        return self.get_external("ols").get("version")

    def get_short_description(self, use_markdown: bool = False) -> str | None:
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

        rv = removesuffix(removeprefix(markdown(rv), "<p>"), "</p>")
        return markupsafe.Markup(rv)

    def get_bioschemas_jsonld(self) -> dict[str, Any]:
        """Get the BioSchemas JSON-LD."""
        identifiers = [
            f"bioregistry:{self.prefix}",
            *(
                f"{metaprefix}:{metaidentifier}"
                for metaprefix, metaidentifier in self.get_mappings().items()
            ),
        ]

        rv = {
            "@context": "https://schema.org",
            "@type": "Dataset",
            "http://purl.org/dc/terms/conformsTo": {
                "@id": "https://bioschemas.org/profiles/Dataset/1.0-RELEASE",
                "@type": "CreativeWork",
            },
            "@id": f"{BIOREGISTRY_REMOTE_URL}/{self.prefix}",
            "url": self.get_homepage(),
            "name": self.get_name(),
            "description": self.get_description(),
            "identifier": identifiers,
            "keywords": self.get_keywords(),
        }
        version = self.get_version()
        if version:
            rv["version"] = version
        license_url = self.get_license_url()
        if license_url:
            rv["license"] = license_url
        return rv

    def get_ols_config(self, ontology_purl: str | None = None) -> OlsConfig:
        """Get a JSON configuration usable in the OLS."""
        creators = []
        if contact := self.get_contact():
            creators.append(contact.name)
            if self.contact_extras:
                creators.extend(ce.name for ce in self.contact_extras if ce.name)
        else:
            creators = [
                "Converted to OWL by Charles Tapley Hoyt (cthoyt@gmail.com), "
                "no primary contact information is available."
            ]

        description = ""
        if description_ := self.get_description():
            description += description_
        if license_ := self.get_license():
            description += f" Licensed under {license_}."

        ontology_purl = self.get_download()
        if not ontology_purl:
            raise ValueError("no OWL nor OBO download available")

        values = {
            # as per https://github.com/EBISPOT/ols4/pull/896#discussion_r2126144218
            "id": self.prefix,
            "reasoner": "none",
            "oboSlims": False,
            # typo on purpose, since OLS has a typo
            "is_foundary": self.get_obofoundry_prefix() is not None,
            "ontology_purl": ontology_purl,
            ######################################################################
            # The remainder are ontology metadata, which could be part of the    #
            # ontology itself.                                                   #
            #                                                                    #
            # See https://github.com/OBOFoundry/OBOFoundry.github.io/issues/1365 #
            ######################################################################
            # Property: dcterms:creator
            "creator": creators,
            # http://purl.org/vocab/vann/preferredNamespacePrefix
            "preferredPrefix": self.get_preferred_prefix() or self.prefix,
            # Property: dcterms:title
            "title": self.get_name(),
            # Property: dcterms:description
            "description": description,
            # TODO figure out why there's dupicate on `uri` and `homepage`
            "uri": self.get_homepage(),
            # Property:  foaf:homepage
            "homepage": self.get_homepage(),
            # Property: http://usefulinc.com/ns/doap#mailing-list
            "mailing_list": self.get_mailing_list() or self.get_contact_email(),
            # TODO add to OMO
            "label_property": "https://www.w3.org/2000/01/rdf-schema#label",
            # TODO add to OMO
            "definition_property": [
                "http://purl.org/dc/terms/description",
            ],
            # TODO add to OMO
            "synonym_property": [
                "http://www.geneontology.org/formats/oboInOwl#hasExactSynonym",
                "http://www.geneontology.org/formats/oboInOwl#hasNarrowSynonym",
                "http://www.geneontology.org/formats/oboInOwl#hasBroadSynonym",
                "http://www.geneontology.org/formats/oboInOwl#hasCloseSynonym",
            ],
            # See https://github.com/information-artifact-ontology/ontology-metadata/pull/193
            "hierarchical_property": [
                "https://www.w3.org/2000/01/rdf-schema#subClassOf",
            ],
            "hidden_property": [],
            # http://purl.org/vocab/vann/preferredNamespaceUri
            "base_uri": [
                self.get_rdf_uri_prefix() or self.get_uri_prefix(),
            ],
            # TODO root terms IAO_0000700 (preferred_root_term)
        }
        return OlsConfig.model_validate(values)


class OlsConfig(BaseModel):
    """A configuration for the Ontology Lookup Service (OLS)."""

    id: str
    reasoner: str
    oboSlims: bool  # noqa:N815
    is_foundary: bool
    ontology_purl: str
    creator: list[str]
    preferredPrefix: str  # noqa:N815
    title: str
    description: str
    uri: str | None
    homepage: str | None
    mailing_list: str | None
    label_property: str
    definition_property: list[str]
    synonym_property: list[str]
    hierarchical_property: list[str]
    hidden_property: list[str]
    base_uri: list[str]


SchemaStatus = Literal["required", "required*", "present", "present*", "missing"]
schema_status_map = {
    True: "🟢",
    False: "🔴",
    "required": "🟢",
    "required*": "🟢*",
    "present": "🟡",
    "present*": "🟡*",
    "missing": "🔴",
}
schema_score_map = {
    "required": 3,
    "required*": 3,
    "present": 1,
    "present*": 2,
    "missing": -1,
}


class RegistryGovernance(BaseModel):
    """Metadata about a registry's governance."""

    curation: Literal["private", "import", "community", "opaque-review", "open-review"]
    curates: bool = Field(
        ...,
        description="This field denotes if the registry's maintainers and "
        "potentially contributors curate novel prefixes.",
    )
    imports: bool = Field(
        ...,
        description="This field denotes if the registry imports and aligns prefixes from other registries.",
    )
    scope: str = Field(
        ...,
        description="This field denotes the scope of prefixes which the registry covers. For example,"
        " some registries are limited to ontologies, some have a full scope over the life sciences,"
        " and some are general purpose.",
    )
    comments: str | None = Field(
        default=None,
        description="Optional additional comments about the registry's governance model",
    )
    accepts_external_contributions: bool = Field(
        ...,
        description="This field denotes if the registry (in theory) accepts external contributions, either via "
        "suggestion or proactive improvement. This field does not pass judgement on the difficult of this"
        " process from the perspective of the submitter nor the responsiveness of the registry."
        " This field does not consider the ability for insiders (i.e., people with private relationships"
        " to the maintainers) to affect change.",
    )
    public_version_controlled_data: bool = Field(
        ...,
        title="Public Version-Controlled Data",
        description="This field denotes if the registry stores its data in publicly available version control"
        " system, such as GitHub or GitLab",
    )
    data_repository: str | None = Field(
        default=None,
        description="This field denotes the address of the registry's data version control repository.",
    )
    code_repository: str | None = Field(
        default=None,
        description="This field denotes the address of the registry's code version control repository.",
    )
    review_team: Literal["public", "inferrable", "private", "democratic", "n/a"] = Field(
        ...,
        description="This field denotes if the registry's reviewers/moderators for external contributions known? If "
        "there's a well-defined, maintained listing, then it can be marked as public. If it can be inferred, e.g. from "
        "reading the commit history on a version control system, then it can be marked as inferrable. A closed"
        " review team, e.g., like for Identifiers.org can be marked as private. Resources that do not"
        " accept external contributions can be marked with N/A. An unmoderated regitry like Prefix.cc is marked with "
        " 'democratic'.",
    )
    status: Literal["active", "unresponsive", "inactive"] = Field(
        ...,
        description="This field denotes the maitenance status of the repository. An active repository is still being "
        "maintained and also is responsive to external requests for improvement. An unresponsive repository is still "
        "being maintained in some capacity but is not responsive to external requests for improvement. An inactive "
        "repository is no longer being proactively maintained (though may receive occasional patches).",
    )
    issue_tracker: str | None = Field(
        default=None,
        description="This field denotes the public issue tracker for issues related to the code and data of the "
        "repository.",
    )

    @property
    def review_team_icon(self) -> str:
        """Get an icon for the review team."""
        if self.review_team == "public":
            return "Y"
        elif self.review_team == "inferrable":
            return "Y*"
        elif self.review_team == "private":
            return "x"
        else:
            return ""

    def score(self) -> int:
        """Get the governance score."""
        _r = {"public": 2, "inferrable": 1, "private": 0, "n/a": 0, "democratic": 2}
        return sum(
            [
                self.accepts_external_contributions,
                self.public_version_controlled_data,
                self.code_repository is not None,
                self.data_repository is not None,
                _r[self.review_team],
                self.status == "active",
                self.issue_tracker is not None,
                -1 if self.scope == "internal" else 0,
            ]
        )


class RegistryQualities(BaseModel):
    """Qualities about a registry."""

    structured_data: bool = Field(
        ...,
        description="This field denotes if the registry provides structured access to its data? For example,"
        " this can be through an API (e.g., FAIRsharing, OLS) or a bulk download (e.g., OBO Foundry) in a "
        "structured file format. A counter-example is a site that must be scraped to acquire its content "
        "(e.g, the NCBI GenBank).",
    )
    bulk_data: bool = Field(
        ...,
        description="This field denotes if the registry provides a bulk dump of its data? For example,"
        " the OBO Foundry provides its bulk data in a file and Identifiers.org provides its bulk data in"
        " an API endpoint. A counterexample is FAIRsharing, which requires slow, expensive pagination"
        " through its data. Another counterexample is HL7 which requires manually navigating a form to"
        " download its content. While GenBank is not structured, it is still bulk downloadable.",
    )
    no_authentication: bool = Field(
        ...,
        description="This field denotes if the registry provides access to its data without an API key? For example,"
        " Identifiers.org. As a counter-example, BioPortal requires an API key for access to its structured data.",
    )
    automatable_download: bool = Field(
        default=True,
        description="This field denotes if the registry makes its data available downloadable in an automated way?"
        "This includes websites that have bulk downloads, paginated API downloads, or even require scraping."
        "A counter example is HL7, whose download can not be automated due to the need to interact with a web"
        " form.",
    )

    def score(self) -> int:
        """Score qualities of a registry."""
        return sum(
            [
                self.structured_data,
                self.bulk_data,
                self.no_authentication,
                self.automatable_download,
            ]
        )


class RegistrySchema(BaseModel):
    """Metadata about a registry's schema."""

    name: SchemaStatus = Field(
        ...,
        description="This field denotes if a name is required, optional, "
        "or never captured for each record in the registry.",
    )
    homepage: SchemaStatus = Field(
        ...,
        description="This field denotes if a homepage is required, optional, "
        "or never captured for each record in the registry.",
    )
    description: SchemaStatus = Field(
        ...,
        description="This field denotes if a description is required, optional, "
        "or never captured for each record in the registry.",
    )
    example: SchemaStatus = Field(
        ...,
        description="This field denotes if an example local unique identifier is "
        "required, optional, or never captured for each record in the registry.",
    )
    pattern: SchemaStatus = Field(
        ...,
        description="This field denotes if a regular expression pattern for matching "
        "local unique identifiers is required, optional, or never captured for each record in the registry.",
    )
    provider: SchemaStatus = Field(
        ...,
        description="This field denotes if a URI format string for converting local "
        "unique identifiers into URIs is required, optional, or never captured for each record in the registry.",
    )
    alternate_providers: Literal["present", "missing"] = Field(
        ...,
        description="This field denotes if additional/secondary URI format strings "
        "for converting local unique identifiers into URIs is required, optional, or never captured for "
        "each record in the registry.",
    )
    synonyms: Literal["present", "missing"] = Field(
        ...,
        description="This field denotes if alternative prefixes (e.g., taxonomy for NCBITaxon) "
        "is required, optional, or never captured for each record in the registry.",
    )
    license: SchemaStatus = Field(
        ...,
        description="This field denotes if capturing the data license is required, optional, "
        "or never captured for each record in the registry.",
    )
    version: SchemaStatus = Field(
        ...,
        description="This field denotes if capturing the current data version is required, "
        "optional, or never captured for each record in the registry.",
    )
    contact: SchemaStatus = Field(
        ...,
        description="This field denotes if capturing the primary responsible person's contact "
        "information (e.g., name, ORCID, email) is required, optional, or never captured for each "
        "record in the registry.",
    )
    search: bool = Field(
        ...,
        title="Prefix Search",
        description="This field denotes if the registry provides either a dedicated page for searching for prefixes "
        "(e.g. AberOWL has a dedicated search page) OR a contextual search (e.g., AgroPortal "
        "has a prefix search built in its homepage).",
    )

    def score(self) -> int:
        """Calculate a score for the metadata availability in the registry."""
        return sum(
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
    bibtex: str | None = Field(
        default=None, description="Citation key used in BibTex for this registry."
    )
    availability: RegistrySchema | None = Field(
        None, description="A structured description of the metadata that the registry collects"
    )
    qualities: RegistryQualities | None = Field(
        None, description="A structured description of the registry's qualities"
    )
    governance: RegistryGovernance | None = Field(
        None, description="A structured description of the governance for the registry"
    )
    download: str | None = Field(
        default=None, description="A download link for the data contained in the registry"
    )
    provider_uri_format: str | None = Field(
        default=None, description="A URL with a $1 for a prefix to resolve in the registry"
    )
    search_uri_format: str | None = Field(
        default=None,
        description="A URL with a $1 for a prefix or string for searching for prefixes",
    )
    resolver_uri_format: str | None = Field(
        default=None,
        description="A URL with a $1 for a prefix and $2 for an identifier to resolve in the registry",
    )
    resolver_type: str | None = Field(
        default=None,
        description="An optional type annotation for what kind of resolver it is (i.e., redirect or lookup)",
    )
    contact: Attributable = Field(..., description="The contact for the registry.")
    bioregistry_prefix: str | None = Field(
        default=None, description="The prefix for this registry in the Bioregistry"
    )
    logo_url: str | None = Field(
        default=None,
        description="The URL for the logo of the resource",
    )
    license: str | None = Field(
        default=None,
        description="The license under which the resource is redistributed",
    )
    short_name: str | None = Field(
        default=None, description="A short name for the resource, e.g., for use in charts"
    )

    def score(self) -> int | None:
        """Calculate a metadata score/goodness for this registry."""
        if self.availability is None or self.qualities is None:
            return None
        return (
            (
                int(self.provider_uri_format is not None)
                + int(self.resolver_uri_format is not None)
                + int(self.download is not None)
                + int(self.contact is not None)
            )
            + self.availability.score()
            + self.qualities.score()
        )

    def get_provider_uri_prefix(self) -> str:
        """Get provider URI prefix.

        :returns: The URI prefix for the provider for prefixes in this registry.

        >>> from bioregistry import get_registry
        >>> get_registry("fairsharing").get_provider_uri_prefix()
        'https://fairsharing.org/'
        >>> get_registry("miriam").get_provider_uri_prefix()
        'https://registry.identifiers.org/registry/'
        >>> get_registry("n2t").get_provider_uri_prefix()
        'https://bioregistry.io/metaregistry/n2t/resolve/'
        """
        if self.provider_uri_format is None or not self.provider_uri_format.endswith("$1"):
            return f"{BIOREGISTRY_REMOTE_URL}/metaregistry/{self.prefix}/resolve/"
        return self.provider_uri_format.replace("$1", "")

    def get_provider_uri_format(self, external_prefix: str) -> str | None:
        """Get the provider string.

        :param external_prefix: The prefix used in the metaregistry

        :returns: The URL in the registry for the prefix, if it's able to provide one

        >>> from bioregistry import get_registry
        >>> get_registry("fairsharing").get_provider_uri_format("FAIRsharing.62qk8w")
        'https://fairsharing.org/FAIRsharing.62qk8w'
        >>> get_registry("miriam").get_provider_uri_format("go")
        'https://registry.identifiers.org/registry/go'
        >>> get_registry("n2t").get_provider_uri_format("go")
        'https://bioregistry.io/metaregistry/n2t/resolve/go'
        """
        return self.get_provider_uri_prefix() + external_prefix

    def get_resolver_uri_format(self, prefix: str) -> str:
        """Generate a provider URI string based on mapping through this registry's vocabulary.

        :param prefix: The prefix used in the metaregistry

        :returns: The URI format string to be used for identifiers in the semantic space
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

    def resolve(self, prefix: str, identifier: str) -> str | None:
        """Resolve the registry-specific prefix and identifier.

        :param prefix: The prefix used in the metaregistry
        :param identifier: The identifier in the semantic space

        :returns: The URI format string for the given CURIE.

        >>> from bioregistry import get_registry
        >>> get_registry("miriam").resolve("go", "0032571")
        'https://identifiers.org/go:0032571'
        >>> get_registry("cellosaurus").resolve("go", "0032571")
        'https://bioregistry.io/metaregistry/cellosaurus/go:0032571'
        >>> get_registry("rrid").resolve("AB", "493771")
        'https://scicrunch.org/resolver/RRID:AB_493771'
        """
        return self.get_resolver_uri_format(prefix).replace("$1", identifier)

    def add_triples(self, graph: rdflib.Graph) -> rdflib.term.Node:
        """Add triples to an RDF graph for this registry.

        :param graph: An RDF graph

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

    def get_code_link(self) -> str | None:
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
        return self.resolver_type == "resolver"

    @property
    def is_lookup(self) -> bool:
        """Check if it is a lookup service."""
        return self.resolver_type == "lookup"

    @property
    def has_permissive_license(self) -> bool:
        """Check if the registry has a permissive license."""
        return self.license in {"CC BY 4.0", "CC0", "CC BY 3.0"}

    @property
    def is_prefix_provider(self) -> bool:
        """Check if the registry is a prefix provider."""
        return self.provider_uri_format is not None

    def get_quality_score(self) -> int | None:
        """Get the quality score for this registry."""
        if self.qualities is None or self.availability is None:
            return None
        return self.qualities.score() + sum(
            [self.availability.search, self.is_prefix_provider, self.has_permissive_license]
        )


class CollectionAnnotation(BaseModel):
    """Collection annotation."""

    prefix: str
    comment: str | None = None

    def is_empty(self) -> bool:
        """Check if the collection annotation is empty."""
        return self.comment is None


class Collection(BaseModel):
    """A collection of resources."""

    identifier: str = Field(..., description="The collection's identifier")
    name: str = Field(
        ...,
        description="The name of the collection",
    )
    description: str = Field(
        ...,
        description="A description of the collection",
        min_length=30,
    )
    resources: list[str | CollectionAnnotation] = Field(
        ...,
        description="A list of prefixes of resources appearing in the collection",
        min_length=1,
    )
    contributors: list[Attributable] = Field(
        ...,
        description="A list of authors/contributors to the collection",
        min_length=1,
    )
    maintainers: list[Author] | None = Field(
        None,
        description="A list of maintainers for the collection",
        min_length=1,
    )
    logo: str | None = None
    organizations: list[Organization] | None = Field(
        None,
        description="A list of organizations that contribute to this collection",
        min_length=1,
    )
    context: str | None = Field(default=None, description="The JSON-LD context's name")
    references: list[str] | None = Field(default=None, description="URL references")
    keywords: list[str] | None = None
    mappings: list[Reference] | None = None

    def add_triples(self, graph: rdflib.Graph) -> None:
        """Add triples to an RDF graph for this collection.

        :param graph: An RDF graph

        :returns: The RDF node representing this collection using a Bioregistry IRI.
        """
        from rdflib import Literal
        from rdflib.namespace import DC, DCTERMS, DOAP, FOAF, RDF, RDFS, SDO, XSD

        from .constants import (
            bioregistry_class_to_id,
            bioregistry_collection,
            bioregistry_resource,
        )

        node = bioregistry_collection.term(self.identifier)
        graph.add((node, RDF["type"], bioregistry_class_to_id[self.__class__.__name__]))
        graph.add((node, RDFS["label"], Literal(self.name)))
        graph.add((node, DC.description, Literal(self.description)))

        for contributor in self.contributors:
            contributor_node = contributor.add_triples(graph)
            graph.add((node, DC.contributor, contributor_node))

        for maintainer in self.maintainers or []:
            maintainer_node = maintainer.add_triples(graph)
            graph.add((node, DOAP.maintainer, maintainer_node))

        if self.logo is not None:
            graph.add((node, FOAF.logo, Literal(self.logo, datatype=XSD.anyURI)))

        for keyword in self.keywords or []:
            graph.add((node, SDO.keywords, Literal(keyword)))

        for resource in self.get_prefixes():
            graph.add((node, DCTERMS.hasPart, bioregistry_resource[resource]))

    def as_context_jsonld_str(self) -> str:
        """Get the JSON-LD context as a string from a given collection."""
        return json.dumps(self.as_context_jsonld())

    def as_context_jsonld(self) -> Mapping[str, Mapping[str, str]]:
        """Get the JSON-LD context from a given collection."""
        return {
            "@context": self.as_prefix_map(),
        }

    def get_prefixes(self) -> list[str]:
        """Get prefixes."""
        rv = []
        for resource in self.resources:
            match resource:
                case CollectionAnnotation():
                    rv.append(resource.prefix)
                case str():
                    rv.append(resource)
        return rv

    def get_annotated_prefixes(self) -> list[CollectionAnnotation]:
        """Get annotated prefixes."""
        rv = []
        for resource in self.resources:
            match resource:
                case CollectionAnnotation():
                    rv.append(resource)
                case str():
                    rv.append(CollectionAnnotation(prefix=resource))
        return rv

    def as_prefix_map(self) -> Mapping[str, str]:
        """Get the prefix map for a given collection."""
        from ..uri_format import get_uri_prefix

        rv = {}
        for prefix in self.get_prefixes():
            fmt = get_uri_prefix(prefix)
            if fmt is not None:
                rv[prefix] = fmt
        return rv

    def has_organization_with_ror(self, ror: str) -> bool:
        """Check if there is an organization with a given ROR."""
        return any(organization.ror == ror for organization in self.organizations or [])


def filter_collections(collections: Iterable[Collection], ror: str) -> list[Collection]:
    """Filter collections based on a ROR."""
    return [
        collection_ for collection_ in collections if collection_.has_organization_with_ror(ror)
    ]


class Context(BaseModel):
    """A prescriptive context.

    A prescriptive context contains configuration for generating fit-for-purpose prefix
    maps to serve various communities based on the standard Bioregistry prefix map,
    custom prefix remapping rules, custom URI prefix remapping rules, custom prefix
    maps, and other community-specific logic.
    """

    name: str = Field(
        ...,
        description="The name of the context",
    )
    description: str = Field(
        ...,
        description="A description of the context, can include Markdown",
    )
    maintainers: list[Author] = Field(
        ...,
        description="A list of maintainers for the context",
    )
    prefix_priority: list[str] | None = Field(
        ...,
        description=_dedent(
            """\
            This ordering of metaprefixes (i.e., prefixes for registries)
            is used to determine the priority of which registry's prefixes are used.
            By default, the canonical Bioregistry prefixes are highest priority.
            Add in "preferred" for explicitly using preferred prefixes or "default" for
            explicitly using Bioregistry canonical prefixes.
        """
        ),
    )
    include_synonyms: bool = Field(
        False,
        description="Should synonyms be included in the prefix map?",
    )
    uri_prefix_priority: list[str] | None = Field(
        ...,
        description=_dedent(
            """\
            This ordering of metaprefixes (i.e., prefixes for registries)
            is used to determine the priority of which registry's URI prefixes are used.
            By default, the canonical Bioregistry URI prefixes are highest priority.
         """
        ),
    )
    prefix_remapping: dict[str, str] | None = Field(
        ...,
        description="This is a mapping from canonical Bioregistry prefixes to custom prefixes used in this context.",
    )
    custom_prefix_map: dict[str, str] | None = Field(
        ...,
        description=_dedent(
            """\
            This is a custom prefix map (which contains custom URL/URI expansions) that is added after all other
            logic is applied. Keys must either be canonical Bioregistry prefixes, prefixes used based on the
            given prefix priority, or values in the given prefix remapping.
        """
        ),
    )
    blacklist: list[str] | None = Field(
        ...,
        description="This is a list of canonical Bioregistry prefixes that should not be included in the context.",
    )
    enforce_w3c: bool = Field(False, description="Should w3c prefix synonyms be enforced?")


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
def get_json_schema() -> dict[str, Any]:
    """Get the JSON schema for the bioregistry."""
    rv = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "$id": "https://bioregistry.io/schema.json",
    }
    models = [
        Author,
        Collection,
        Provider,
        Resource,
        Registry,
        RegistrySchema,
        Context,
        Publication,
    ]

    title = "Bioregistry JSON Schema"
    description = (
        "The Bioregistry JSON Schema describes the shapes of the objects in"
        " the registry, metaregistry, collections, and their other related"
        " resources"
    )

    # see https://docs.pydantic.dev/latest/usage/json_schema/#general-notes-on-json-schema-generation
    _, schema_dict = models_json_schema(
        [(model, "validation") for model in models],  # type:ignore
        title=title,
        description=description,
    )

    rv.update(schema_dict)
    return rv


def _get(resource: Resource, key: str) -> Any:
    # TODO delete this function
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
    if isinstance(x, list | set):
        return "|".join(sorted(x))
    return x or ""


DEDP_PUB_KEYS = ("pubmed", "doi", "pmc")


def deduplicate_publications(publications: Iterable[Publication]) -> list[Publication]:
    """Deduplicate publications."""
    records = [publication.model_dump(exclude_none=True) for publication in publications]
    records_deduplicated = deduplicate(records, keys=DEDP_PUB_KEYS)
    return [Publication(**record) for record in records_deduplicated]


@click.command()
def generate_schema() -> None:
    """Dump the JSON schemata."""
    with SCHEMA_PATH.open("w") as file:
        json.dump(get_json_schema(), indent=2, fp=file)


if __name__ == "__main__":
    generate_schema()
