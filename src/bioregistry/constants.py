"""Constants and utilities for registries."""

from __future__ import annotations

import enum
import os
import pathlib
import re
from typing import TypeAlias

import pystow
from curies import ReferenceTuple

__all__ = [
    "BIOREGISTRY_MODULE",
    "BIOREGISTRY_PATH",
    "COLLECTIONS_PATH",
    "CONTEXTS_PATH",
    "CURATED_MAPPINGS_PATH",
    "DATA_DIRECTORY",
    "HERE",
    "INTERNAL_COLOR",
    "INTERNAL_KEY",
    "INTERNAL_LABEL",
    "INTERNAL_METAPREFIX",
    "INTERNAL_PIP",
    "INTERNAL_REPOSITORY",
    "METAREGISTRY_PATH",
    "RAW_DIRECTORY",
    "FailureReturnType",
    "MaybeCURIE",
    "get_failure_return_type",
]

PATTERN_KEY = "pattern"
ORCID_PATTERN = r"^\d{4}-\d{4}-\d{4}-\d{3}(\d|X)$"

HERE = pathlib.Path(os.path.abspath(os.path.dirname(__file__)))
DATA_DIRECTORY = HERE / "data"
EXTERNAL = DATA_DIRECTORY / "external"
BIOREGISTRY_PATH = DATA_DIRECTORY / "bioregistry.json"
METAREGISTRY_PATH = DATA_DIRECTORY / "metaregistry.json"
COLLECTIONS_PATH = DATA_DIRECTORY / "collections.json"
CURATED_MAPPINGS_PATH = DATA_DIRECTORY / "curated_mappings.sssom.tsv"
CONTEXTS_PATH = DATA_DIRECTORY / "contexts.json"
CURATED_PAPERS_PATH = DATA_DIRECTORY / "curated_papers.tsv"

BIOREGISTRY_MODULE = pystow.module("bioregistry")

ROOT = HERE.parent.parent.resolve()
DOCS = ROOT.joinpath("docs")
DOCS_DATA = DOCS.joinpath("_data")
DOCS_IMG = DOCS.joinpath("img")

EXPORT_DIRECTORY = ROOT.joinpath("exports")

METADATA_CURATION_DIRECTORY = EXPORT_DIRECTORY.joinpath("alignment")
RAW_DIRECTORY = EXPORT_DIRECTORY.joinpath("raw")
EXPORT_CONTEXTS = EXPORT_DIRECTORY / "contexts"
CONTEXT_BIOREGISTRY_PATH = EXPORT_CONTEXTS / "bioregistry.context.jsonld"
SHACL_TURTLE_PATH = EXPORT_CONTEXTS / "bioregistry.context.ttl"
CONTEXT_OBO_PATH = EXPORT_CONTEXTS / "obo.context.jsonld"
SHACL_OBO_TURTLE_PATH = EXPORT_CONTEXTS / "obo.context.ttl"
CONTEXT_OBO_SYNONYMS_PATH = EXPORT_CONTEXTS / "obo_synonyms.context.jsonld"
SHACL_OBO_SYNONYMS_TURTLE_PATH = EXPORT_CONTEXTS / "obo_synonyms.context.ttl"

EXPORT_RDF = EXPORT_DIRECTORY.joinpath("rdf")
SCHEMA_SVG_PATH = EXPORT_RDF / "schema.svg"
SCHEMA_PDF_PATH = EXPORT_RDF / "schema.pdf"
SCHEMA_TURTLE_PATH = EXPORT_RDF / "schema.ttl"
SCHEMA_NT_PATH = EXPORT_RDF / "schema.nt"
SCHEMA_JSONLD_PATH = EXPORT_RDF / "schema.jsonld"
RDF_TURTLE_PATH = EXPORT_RDF / "bioregistry.ttl"
RDF_NT_PATH = EXPORT_RDF / "bioregistry.nt"
RDF_JSONLD_PATH = EXPORT_RDF / "bioregistry.jsonld"

EXPORT_SSSOM = EXPORT_DIRECTORY.joinpath("sssom")
SSSOM_PATH = EXPORT_SSSOM / "bioregistry.sssom.tsv"
SSSOM_METADATA_PATH = EXPORT_SSSOM / "bioregistry.sssom.yml"

EXPORT_REGISTRY = EXPORT_DIRECTORY.joinpath("registry")
REGISTRY_YAML_PATH = EXPORT_REGISTRY / "registry.yml"
REGISTRY_JSON_PATH = EXPORT_REGISTRY / "registry.json"
REGISTRY_TSV_PATH = EXPORT_REGISTRY / "registry.tsv"

EXPORT_METAREGISTRY = EXPORT_DIRECTORY.joinpath("metaregistry")
METAREGISTRY_YAML_PATH = EXPORT_METAREGISTRY / "metaregistry.yml"
METAREGISTRY_TSV_PATH = EXPORT_METAREGISTRY / "metaregistry.tsv"

EXPORT_COLLECTIONS = EXPORT_DIRECTORY.joinpath("collections")
COLLECTIONS_YAML_PATH = EXPORT_COLLECTIONS / "collections.yml"
COLLECTIONS_TSV_PATH = EXPORT_COLLECTIONS / "collections.tsv"

EXPORT_TABLES = EXPORT_DIRECTORY.joinpath("tables")
TABLES_GOVERNANCE_TSV_PATH = EXPORT_TABLES.joinpath("comparison_goveranance.tsv")
TABLES_GOVERNANCE_LATEX_PATH = EXPORT_TABLES.joinpath("comparison_goveranance.tex")
TABLES_METADATA_TSV_PATH = EXPORT_TABLES.joinpath("comparison_metadata.tsv")
TABLES_METADATA_LATEX_PATH = EXPORT_TABLES.joinpath("comparison_metadata.tex")
TABLES_SUMMARY_LATEX_PATH = EXPORT_TABLES.joinpath("summary.tex")

EXPORT_ANALYSES = EXPORT_DIRECTORY.joinpath("analyses")

BENCHMARKS = EXPORT_DIRECTORY.joinpath("benchmarks")

URI_PARSING = BENCHMARKS.joinpath("uri_parsing")
URI_PARSING_DATA_PATH = URI_PARSING.joinpath("data.tsv")
URI_PARSING_SVG_PATH = URI_PARSING.joinpath("results.svg")

CURIE_PARSING = BENCHMARKS.joinpath("curie_parsing")
CURIE_PARSING_DATA_PATH = CURIE_PARSING.joinpath("data.tsv")
CURIE_PARSING_SVG_PATH = CURIE_PARSING.joinpath("results.svg")

CURIE_VALIDATION = BENCHMARKS.joinpath("curie_validation")
CURIE_VALIDATION_DATA_PATH = CURIE_VALIDATION.joinpath("data.tsv")
CURIE_VALIDATION_SVG_PATH = CURIE_VALIDATION.joinpath("results.svg")

BIOREGISTRY_DEFAULT_BASE_URL = "https://bioregistry.io"
#: The URL of the remote Bioregistry site
BIOREGISTRY_REMOTE_URL = pystow.get_config(
    "bioregistry", "url", default=BIOREGISTRY_DEFAULT_BASE_URL
)

#: Resolution is broken on identifiers.org for the following
IDOT_BROKEN = {
    "gramene.growthstage",
    "oma.hog",
    "mir",  # Added on 2021-10-08
    "storedb",  # Added on 2021-10-12
    "miriam.collection",  # Added on 2022-09-17
    "miriam.resource",  # Added on 2022-09-17
    "psipar",  # Added on 2022-09-17
}

URI_FORMAT_KEY = "uri_format"

#: MIRIAM definitions that don't make any sense
MIRIAM_BLACKLIST = {
    # this one uses the names instead of IDs, and points to a dead resource.
    # See https://github.com/identifiers-org/identifiers-org.github.io/issues/139
    "pid.pathway",
    # this uses namespace-in-namespace
    "neurolex",
    # Miriam needs to be extended
    "ccds",
    # Miriam completely misses the actual usage
    "agricola",
    # Miriam pattern/example combo is broken
    # See https://github.com/biopragmatics/bioregistry/issues/1588
    "hogenom",
    # Miriam pattern/example combo is broken
    "homd.seq",
}
IDENTIFIERS_ORG_URL_PREFIX = "https://identifiers.org/"

#: The priority list
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
NDEX_UUID = "860647c4-f7c1-11ec-ac45-0ac135e8bacf"

SHIELDS_BASE = "https://img.shields.io/badge/dynamic"
CH_BASE = "https://cthoyt.com/obo-community-health"
HEALTH_BASE = "https://github.com/cthoyt/obo-community-health/raw/main/data/data.json"
EXTRAS = f"%20Community%20Health%20Score&link={CH_BASE}"

# not a perfect email regex, but close enough
EMAIL_RE_STR = r"^(\w|\.|\_|\-)+[@](\w|\_|\-|\.)+[.]\w{2,7}$"
EMAIL_RE = re.compile(EMAIL_RE_STR)

NonePair: TypeAlias = tuple[None, None]

MaybeCURIE = ReferenceTuple | NonePair | None

DISALLOWED_EMAIL_PARTS = {
    "contact@",
    "help@",
    "helpdesk@",
    "discuss@",
    "support@",
}


class FailureReturnType(enum.Enum):
    """A flag for what to return when handling reference tuples."""

    #: return a single None
    single = enum.auto()
    #: return a pair of None's
    pair = enum.auto()


def get_failure_return_type(frt: FailureReturnType) -> None | NonePair:
    """Get the right failure return type."""
    if frt == FailureReturnType.single:
        return None
    elif frt == FailureReturnType.pair:
        return None, None
    raise TypeError


SCHEMA_CURIE_PREFIX = "bioregistry.schema"
SCHEMA_URI_PREFIX = "https://bioregistry.io/schema/#"
INTERNAL_MASTODON_SERVER = "hackyderm.io"
INTERNAL_MASTODON_HANDLE = "bioregistry"
INTERNAL_MASTODON = f"{INTERNAL_MASTODON_HANDLE}@{INTERNAL_MASTODON_SERVER}"
INTERNAL_METAPREFIX = "bioregistry"
INTERNAL_KEY = "bioregistry"
INTERNAL_PIP = "bioregistry"
INTERNAL_LABEL = "Bioregistry"
INTERNAL_REPOSITORY_SLUG = "biopragmatics/bioregistry"
INTERNAL_REPOSITORY_PAGES = "https://biopragmatics.github.io/bioregistry"
INTERNAL_REPOSITORY = f"https://github.com/{INTERNAL_REPOSITORY_SLUG}"
INTERNAL_REPOSITORY_BLOB = f"https://github.com/{INTERNAL_REPOSITORY_SLUG}/blob/main"
INTERNAL_REPOSITORY_RAW = f"https://raw.githubusercontent.com/{INTERNAL_REPOSITORY_SLUG}/main"
INTERNAL_DOCKERHUB_SLUG = "biopragmatics/bioregistry"
#: see named colors https://matplotlib.org/stable/gallery/color/named_colors.html
INTERNAL_COLOR = "silver"
SSSOM_METADATA = {
    "license": "https://creativecommons.org/publicdomain/zero/1.0/",
    "mapping_set_id": "https://github.com/biopragmatics/bioregistry/raw/main/exports/sssom/bioregistry.sssom.tsv",
    "mapping_set_title": INTERNAL_LABEL,
}
APPEARS_IN_PRED = ReferenceTuple(SCHEMA_CURIE_PREFIX, "0000018")
DEPENDS_ON_PRED = ReferenceTuple(SCHEMA_CURIE_PREFIX, "0000017")
PROVIDES_PRED = ReferenceTuple(SCHEMA_CURIE_PREFIX, "0000011")
HAS_CANONICAL_PRED = ReferenceTuple(SCHEMA_CURIE_PREFIX, "0000016")

POWERED_BY_BIOREGISTRY_IMAGE = "image/png;base64,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"
