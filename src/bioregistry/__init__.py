# -*- coding: utf-8 -*-

"""Extract registry information."""

from .resolve import (  # noqa
    get, get_format, get_name, get_pattern, get_version, get_versions, is_deprecated, normalize_prefix,
)
from .utils import read_bioregistry  # noqa
