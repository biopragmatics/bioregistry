# -*- coding: utf-8 -*-

"""Utility functions for the Bioregistry :mod:`flask` app."""

import itertools as itt
from typing import Optional

from flask import abort, redirect, url_for

import bioregistry


def _get_resource_providers(prefix: str, identifier: str):
    if identifier is None:
        return
    rv = []
    for metaprefix, url in bioregistry.get_providers(prefix, identifier).items():
        if metaprefix == 'default':
            metaprefix = prefix
            name = bioregistry.get_name(prefix)
            homepage = bioregistry.get_homepage(prefix)
        else:
            name = bioregistry.get_registry_name(metaprefix)
            homepage = bioregistry.get_registry_homepage(metaprefix)
        rv.append(dict(
            metaprefix=metaprefix,
            homepage=homepage,
            name=name,
            url=url,
        ))
    return rv


def _get_resource_mapping_rows(prefix: str):
    mappings = bioregistry.get_mappings(prefix)
    if mappings is None:
        return None
    return [
        dict(
            metaprefix=metaprefix,
            xref=xref,
            homepage=bioregistry.get_registry_homepage(metaprefix),
            name=bioregistry.get_registry_name(metaprefix),
            url=bioregistry.get_registry_url(metaprefix, xref),
        )
        for metaprefix, xref in itt.chain(
            [('bioregistry', prefix)],
            mappings.items(),
        )
    ]


def _normalize_prefix_or_404(prefix: str, endpoint: Optional[str] = None):
    try:
        norm_prefix = bioregistry.normalize_prefix(prefix)
    except ValueError:
        norm_prefix = None
    if norm_prefix is None:
        abort(404, f'Invalid prefix: {prefix}')
    elif endpoint is not None and norm_prefix != prefix:
        return redirect(url_for(endpoint, prefix=norm_prefix))
    return norm_prefix
