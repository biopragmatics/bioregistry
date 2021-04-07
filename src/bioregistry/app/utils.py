# -*- coding: utf-8 -*-

"""Utility functions for the Bioregistry :mod:`flask` app."""

from flask import abort

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
        for metaprefix, xref in mappings.items()
    ]


def _normalize_prefix_or_404(prefix: str) -> str:
    norm_prefix = bioregistry.normalize_prefix(prefix)
    if norm_prefix is None:
        abort(404)
    return norm_prefix
