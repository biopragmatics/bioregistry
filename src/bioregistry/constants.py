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

DOCS = HERE.parent.parent.joinpath("docs").resolve()
DOCS_DATA = DOCS.joinpath("_data")
DOCS_IMG = DOCS.joinpath("img")

#: The URL of the remote Bioregistry site
BIOREGISTRY_REMOTE_URL = pystow.get_config("bioregistry", "url") or "https://bioregistry.io"

#: Resolution is broken on identifiers.org for the following
IDOT_BROKEN = {
    "gramene.growthstage",
    "oma.hog",
    "obi",
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
