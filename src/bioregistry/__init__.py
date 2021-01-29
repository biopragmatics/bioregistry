# -*- coding: utf-8 -*-

"""Extract registry information."""

from .resolve import (  # noqa
    get, get_example, get_format, get_name, get_pattern, get_pattern_re, get_version, get_versions, is_deprecated,
    namespace_in_lui, normalize_prefix, validate,
)
from .utils import read_bioregistry  # noqa
