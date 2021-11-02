# -*- coding: utf-8 -*-

"""Constants and utilities for registries."""

import os
import pathlib

import pystow

__all__ = [
    "HERE",
    "DATA_DIRECTORY",
    "BIOREGISTRY_PATH",
    "METAREGISTRY_PATH",
    "COLLECTIONS_PATH",
    "MISMATCH_PATH",
    "BIOREGISTRY_MODULE",
    "LICENSES",
]

HERE = pathlib.Path(os.path.abspath(os.path.dirname(__file__)))
DATA_DIRECTORY = HERE / "data"
BIOREGISTRY_PATH = DATA_DIRECTORY / "bioregistry.json"
METAREGISTRY_PATH = DATA_DIRECTORY / "metaregistry.json"
COLLECTIONS_PATH = DATA_DIRECTORY / "collections.json"
MISMATCH_PATH = DATA_DIRECTORY / "mismatch.json"

BIOREGISTRY_MODULE = pystow.module("bioregistry")

ROOT = HERE.parent.parent.resolve()
DOCS = ROOT.joinpath("docs")
DOCS_DATA = DOCS.joinpath("_data")
DOCS_IMG = DOCS.joinpath("img")


EXPORT_DIRECTORY = ROOT.joinpath("exports")

EXPORT_CONTEXTS = EXPORT_DIRECTORY / "contexts"
CONTEXT_OBO_PATH = EXPORT_CONTEXTS / "obo.context.jsonld"
CONTEXT_OBO_SYNONYMS_PATH = EXPORT_CONTEXTS / "obo_synonyms.context.jsonld"

EXPORT_RDF = EXPORT_DIRECTORY.joinpath("rdf")
RDF_TURTLE_PATH = EXPORT_RDF / "bioregistry.ttl"
RDF_NT_PATH = EXPORT_RDF / "bioregistry.nt"
RDF_JSONLD_PATH = EXPORT_RDF / "bioregistry.jsonld"

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

#: The URL of the remote Bioregistry site
BIOREGISTRY_REMOTE_URL = pystow.get_config("bioregistry", "url") or "https://bioregistry.io"

#: Resolution is broken on identifiers.org for the following
IDOT_BROKEN = {
    "gramene.growthstage",
    "oma.hog",
    "obi",
    "mir",  # Added on 2021-10-08
    "storedb",  # Added on 2021-10-12
}

LICENSES = {
    "None": None,
    "license": None,
    "unspecified": None,
    # CC-BY (4.0)
    "CC-BY 4.0": "CC-BY-4.0",
    "CC BY 4.0": "CC-BY-4.0",
    "https://creativecommons.org/licenses/by/4.0/": "CC-BY-4.0",
    "http://creativecommons.org/licenses/by/4.0/": "CC-BY-4.0",
    "http://creativecommons.org/licenses/by/4.0": "CC-BY-4.0",
    "https://creativecommons.org/licenses/by/3.0/": "CC-BY-4.0",
    "url: http://creativecommons.org/licenses/by/4.0/": "CC-BY-4.0",
    "SWO is provided under a Creative Commons Attribution 4.0 International"
    " (CC BY 4.0) license (https://creativecommons.org/licenses/by/4.0/).": "CC-BY-4.0",
    # CC-BY (3.0)
    "CC-BY 3.0 https://creativecommons.org/licenses/by/3.0/": "CC-BY-3.0",
    "http://creativecommons.org/licenses/by/3.0/": "CC-BY-3.0",
    "CC-BY 3.0": "CC-BY-3.0",
    "CC BY 3.0": "CC-BY-3.0",
    "CC-BY version 3.0": "CC-BY-3.0",
    # CC-BY (2.0)
    "CC-BY 2.0": "CC-BY",
    # CC-BY (unversioned)
    "CC-BY": "CC-BY",
    "creative-commons-attribution-license": "CC-BY",
    # CC 0
    "CC-0": "CC-0",
    "CC0 1.0 Universal": "CC-0",
    "CC0": "CC-0",
    "http://creativecommons.org/publicdomain/zero/1.0/": "CC-0",
    "https://creativecommons.org/publicdomain/zero/1.0/": "CC-0",
    # CC-BY-SA
    "CC-BY-SA": "Other",
    "https://creativecommons.org/licenses/by-sa/4.0/": "Other",
    # CC-BY-NC-SA
    "http://creativecommons.org/licenses/by-nc-sa/2.0/": "Other",
    # Apache 2.0
    "Apache 2.0 License": "Other",
    "LICENSE-2.0": "Other",
    "www.apache.org/licenses/LICENSE-2.0": "Other",
    # GPL
    "GNU GPL 3.0": "Other",
    "GPL-3.0": "Other",
    # BSD
    "New BSD license": "Other",
    # Other
    "hpo": "Other",
    "Artistic License 2.0": "Other",
}

URI_FORMAT_KEY = "uri_format"
