# -*- coding: utf-8 -*-

"""Utility functions for the Bioregistry :mod:`flask` app."""

import itertools as itt
from typing import Any, List, Mapping, Optional

from flask import abort, redirect, render_template, url_for

import bioregistry
from bioregistry.constants import BIOREGISTRY_REMOTE_URL


def _get_resource_providers(prefix: str, identifier: str):
    if identifier is None:
        return
    rv = []
    for metaprefix, url in bioregistry.get_providers_list(prefix, identifier):
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
        return render_template('resolve_missing_prefix.html', prefix=prefix), 404
    elif endpoint is not None and norm_prefix != prefix:
        return redirect(url_for(endpoint, prefix=norm_prefix))
    return norm_prefix


def _search(q: str) -> List[str]:
    q_norm = q.lower()
    return [
        prefix
        for prefix in bioregistry.read_bioregistry()
        if q_norm in prefix
    ]


def _autocomplete(q: str) -> Mapping[str, Any]:
    r"""Run the autocomplete algorithm.

    :param q: The query string
    :return: A dictionary with the autocomplete results.

    Before completion is of prefix:

    >>> _autocomplete('cheb')
    {"query": "chebi", "reason": "searched prefix", results=["chebi"], success: True, url: None}

    If only prefix is complete:

    >>> _autocomplete('chebi')
    {"query": "chebi", "reason": "matched prefix", results=["chebi"], success: True, url: "https://bioregistry.io/chebi"}

    Not matching the pattern:

    >>> _autocomplete('chebi:NOPE')
    {"identifier": "NOPE", "pattern": "^CHEBI:\\d+$", "prefix": "chebi", "query": "chebi:NOPE", "reason": "failed validation", "success": False, "url": None}

    Matching the pattern:

    >>> _autocomplete('chebi:1234')
    {"identifier":"1234", "pattern": "^CHEBI:\\d+$", "prefix": "chebi", "query": "chebi:1234", "reason": "passed validation", "success": True, "url": "https://bioregistry.io/chebi:1234"}
    """  # noqa: E501
    if ':' not in q:
        url: Optional[str]
        if q in bioregistry.read_bioregistry():
            reason = 'matched prefix'
            url = f'{BIOREGISTRY_REMOTE_URL.rstrip()}/{q}'
        else:
            reason = 'searched prefix'
            url = None
        return dict(
            query=q,
            results=_search(q),
            success=True,
            reason=reason,
            url=url,
        )
    prefix, identifier = q.split(':', 1)
    norm_prefix = bioregistry.normalize_prefix(prefix)
    if norm_prefix is None:
        return dict(
            query=q,
            prefix=prefix,
            identifier=identifier,
            success=False,
            reason='bad prefix',
        )
    pattern = bioregistry.get_pattern(prefix)
    if pattern is None:
        success = True
        reason = 'no pattern'
        url = bioregistry.resolve_identifier._get_bioregistry_link(prefix, identifier)
    elif bioregistry.validate(prefix, identifier):
        success = True
        reason = 'passed validation'
        url = bioregistry.resolve_identifier._get_bioregistry_link(prefix, identifier)
    else:
        success = False
        reason = 'failed validation'
        url = None
    return dict(
        query=q,
        prefix=prefix,
        pattern=pattern,
        identifier=identifier,
        success=success,
        reason=reason,
        url=url,
    )


def _get_identifier(prefix: str, identifier: str) -> Mapping[str, Any]:
    prefix = _normalize_prefix_or_404(prefix)
    if not bioregistry.validate(prefix, identifier):
        return abort(404, f'invalid identifier: {prefix}:{identifier} for pattern {bioregistry.get_pattern(prefix)}')
    providers = bioregistry.get_providers(prefix, identifier)
    if not providers:
        return abort(404, f'no providers available for {prefix}:{identifier}')

    return dict(
        query=dict(prefix=prefix, identifier=identifier),
        providers=providers,
    )
