# -*- coding: utf-8 -*-

"""Download Prefix Commons."""

import requests

__all__ = [
    'get_prefix_commons',
]

URL = 'https://raw.githubusercontent.com/prefixcommons/biocontext/master/registry/commons_context.jsonld'


def get_prefix_commons():
    """Get Prefix Commons."""
    return {
        prefix: {'formatter': f'{url}$1'}
        for prefix, url in requests.get(URL).json()['@context'].items()
    }
