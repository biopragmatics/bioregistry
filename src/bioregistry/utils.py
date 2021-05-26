# -*- coding: utf-8 -*-

"""Utilities."""

import json
import logging
import warnings
from copy import deepcopy
from datetime import datetime
from functools import lru_cache, wraps
from typing import Any, List, Mapping

import click
import requests

from .constants import BIOREGISTRY_PATH, COLLECTIONS_PATH, METAREGISTRY_PATH, MISMATCH_PATH

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def read_metaregistry() -> Mapping[str, Mapping[str, Any]]:
    """Read the metaregistry as JSON."""
    with open(METAREGISTRY_PATH, encoding='utf-8') as file:
        return {
            entry['prefix']: entry
            for entry in json.load(file)
        }


def read_bioregistry():
    """Read the Bioregistry as JSON."""
    warnings.warn('Renamed read_bioregistry() to read_registry(). Will remove soon.', DeprecationWarning)
    return read_registry()


@lru_cache(maxsize=1)
def read_registry():
    """Read the Bioregistry as JSON."""
    with open(BIOREGISTRY_PATH, encoding='utf-8') as file:
        return json.load(file)


@lru_cache(maxsize=1)
def read_mismatches() -> Mapping[str, Mapping[str, str]]:
    """Read the mismatches as JSON."""
    with MISMATCH_PATH.open() as file:
        return json.load(file)


def is_mismatch(bioregistry_prefix, external_metaprefix, external_prefix) -> bool:
    """Return if the triple is a mismatch."""
    return external_prefix in read_mismatches().get(bioregistry_prefix, {}).get(external_metaprefix, {})


@lru_cache(maxsize=1)
def read_collections():
    """Read the manually curated collections."""
    with open(COLLECTIONS_PATH, encoding='utf-8') as file:
        rv = json.load(file)
    for k, v in rv.items():
        v['identifier'] = k
    return rv


def write_collections(collections):
    """Write the collections."""
    collections = deepcopy(collections)
    for v in collections.values():
        if 'identifier' in v:
            del v['identifier']
        v['resources'] = sorted(set(v['resources']))
    with open(COLLECTIONS_PATH, encoding='utf-8', mode='w') as file:
        json.dump(collections, file, indent=2, sort_keys=True, ensure_ascii=False)


def write_bioregistry(registry):
    """Write to the Bioregistry."""
    with open(BIOREGISTRY_PATH, mode='w', encoding='utf-8') as file:
        json.dump(registry, file, indent=2, sort_keys=True, ensure_ascii=False)


def updater(f):
    """Make a decorator for functions that auto-update the bioregistry."""

    @wraps(f)
    def wrapped():
        registry = read_registry()
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


def secho(s, fg='cyan', bold=True, **kwargs):
    """Wrap :func:`click.secho`."""
    click.echo(f'[{datetime.now().strftime("%H:%M:%S")}] ' + click.style(s, fg=fg, bold=bold, **kwargs))


#: Wikidata SPARQL endpoint. See https://www.wikidata.org/wiki/Wikidata:SPARQL_query_service#Interfacing
WIKIDATA_ENDPOINT = 'https://query.wikidata.org/bigdata/namespace/wdq/sparql'


def query_wikidata(sparql: str) -> List[Mapping[str, Any]]:
    """Query Wikidata's sparql service.

    :param sparql: A SPARQL query string
    :return: A list of bindings
    """
    logger.debug('running query: %s', sparql)
    res = requests.get(WIKIDATA_ENDPOINT, params={'query': sparql, 'format': 'json'})
    res.raise_for_status()
    res_json = res.json()
    return res_json['results']['bindings']
