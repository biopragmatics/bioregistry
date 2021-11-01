# -*- coding: utf-8 -*-

"""Data structures."""

from .constants import (  # noqa:F401
    bioregistry_collection,
    bioregistry_metaresource,
    bioregistry_resource,
    bioregistry_schema,
    bioregistry_schema_terms,
    orcid,
)
from .struct import Author, Collection, Registry, Resource, get_json_schema  # noqa:F401
from .utils import sanitize_mapping, sanitize_model  # noqa:F401
