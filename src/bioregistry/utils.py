# -*- coding: utf-8 -*-

"""Utilities."""

import json
from functools import wraps

from .constants import BIOREGISTRY_PATH


def read_bioregistry():
    """Read the Bioregistry as JSON."""
    with open(BIOREGISTRY_PATH) as file:
        return json.load(file)


def write_bioregistry(registry):
    """Write to the Bioregistry."""
    with open(BIOREGISTRY_PATH, 'w') as file:
        json.dump(registry, file, indent=2, sort_keys=True, ensure_ascii=False)


def updater(f):
    """Make a decorator for functions that auto-update the bioregistry."""

    @wraps(f)
    def wrapped():
        registry = read_bioregistry()
        rv = f(registry)
        if rv is not None:
            write_bioregistry(registry)
        return rv

    return wrapped
