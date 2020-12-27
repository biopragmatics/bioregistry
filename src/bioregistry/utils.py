# -*- coding: utf-8 -*-

"""Utilities."""

import json
import logging
from datetime import datetime
from functools import lru_cache, wraps
from typing import Any, List, Mapping, Optional

import click
import requests

from .constants import BIOREGISTRY_PATH

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
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


def clean_set(*it: Optional[str]):
    """Make a set of the truthy elements in an iterable."""
    return {el for el in it if el}


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
