# -*- coding: utf-8 -*-

"""Utilities for handling external registries."""

import json
import logging
import os
from operator import itemgetter
from typing import List, Mapping, Optional, Union

import requests

from ..constants import EnsureEntry

__all__ = [
    'ensure_registry',
]

logger = logging.getLogger(__name__)


def ensure_registry(
    *,
    url: str,
    embedded_key: str,
    id_key: str,
    cache_path: Optional[str] = None,
    mappify: bool = False,
    force_download: bool = False,
    skip_deprecated: bool = False,
    deprecated_key: Optional[str] = None,
) -> Union[List[EnsureEntry], Mapping[str, EnsureEntry]]:
    """Download the registry (works for MIRIAM and OLS) if it doesn't already exist."""
    if not force_download and cache_path is not None and os.path.exists(cache_path):
        with open(cache_path) as file:
            rv = json.load(file)
    else:
        rv = _download_paginated(url, embedded_key=embedded_key)
        rv = sorted(rv, key=itemgetter(id_key))
        if cache_path is not None:
            with open(cache_path, 'w') as file:
                json.dump(rv, file, indent=2, sort_keys=True)

    if skip_deprecated and deprecated_key:
        rv = [
            entry
            for entry in rv
            if not entry.get(deprecated_key, False)
        ]

    if mappify:
        rv = list_to_map(rv, id_key)

    return rv


def list_to_map(entries, key):
    """Turn a list into a map."""
    return {entry[key]: entry for entry in entries}


def _download_paginated(start_url: str, embedded_key: str) -> List[EnsureEntry]:
    results = []
    url = start_url
    while True:
        logger.debug('getting %s', url)
        g = requests.get(url)
        j = g.json()
        r = j['_embedded'][embedded_key]
        results.extend(r)
        links = j['_links']
        if 'next' not in links:
            break
        url = links['next']['href']
    return results
