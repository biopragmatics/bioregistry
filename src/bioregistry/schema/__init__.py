# -*- coding: utf-8 -*-

"""Data structures."""

from .struct import (  # noqa:F401
    Attributable,
    Author,
    Collection,
    Context,
    Publication,
    Registry,
    Resource,
    get_json_schema,
)
from .utils import sanitize_mapping, sanitize_model  # noqa:F401
