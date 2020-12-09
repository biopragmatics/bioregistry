# -*- coding: utf-8 -*-

"""Utilities."""

import json
from datetime import datetime
from functools import wraps

import click

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


def norm(s: str) -> str:
    """Normalize a string for dictionary key usage."""
    rv = s.lower()
    for x in ' .-':
        rv = rv.replace(x, '')
    return rv


def clean_set(it):
    """Make a set of the truthy elements in an iterable."""
    return {el for el in it if el}


def secho(s, fg='cyan', bold=True, **kwargs):
    """Wrap :func:`click.secho`."""
    click.secho(f'[{datetime.now().strftime("%H:%M:%S")}] {s}', fg=fg, bold=bold, **kwargs)
