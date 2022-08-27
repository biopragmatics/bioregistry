# -*- coding: utf-8 -*-

"""Utility functions for the Bioregistry :mod:`flask` app."""

import json
from typing import Any, Callable, Dict, List, Mapping, Optional, Sequence, Tuple

import yaml
from flask import abort, current_app, redirect, render_template, request, url_for
from pydantic import BaseModel

from bioregistry.constants import BIOREGISTRY_REMOTE_URL
from bioregistry.schema import Resource, sanitize_model
from bioregistry.utils import curie_to_str, extended_encoder

from .proxies import manager


def _get_resource_providers(
    prefix: str, identifier: Optional[str]
) -> Optional[List[Dict[str, Any]]]:
    if identifier is None:
        return None
    rv = []
    for metaprefix, uri in manager.get_providers_list(prefix, identifier):
        if metaprefix == "default":
            metaprefix = prefix
            name = manager.get_name(prefix)
            homepage = manager.get_homepage(prefix)
        else:
            name = manager.get_registry_name(metaprefix)
            homepage = manager.get_registry_homepage(metaprefix)
        rv.append(
            dict(
                metaprefix=metaprefix,
                homepage=homepage,
                name=name,
                uri=uri,
            )
        )
    return rv


def _get_resource_mapping_rows(resource: Resource) -> List[Mapping[str, Any]]:
    return [
        dict(
            metaprefix=metaprefix,
            metaresource=manager.get_registry(metaprefix),
            xref=xref,
            homepage=manager.get_registry_homepage(metaprefix),
            name=manager.get_registry_name(metaprefix),
            uri=manager.get_registry_provider_uri_format(metaprefix, xref),
        )
        for metaprefix, xref in resource.get_mappings().items()
    ]


def _normalize_prefix_or_404(prefix: str, endpoint: Optional[str] = None):
    try:
        norm_prefix = manager.normalize_prefix(prefix)
    except ValueError:
        norm_prefix = None
    if norm_prefix is None:
        return render_template("resolve_errors/missing_prefix.html", prefix=prefix), 404
    elif endpoint is not None and norm_prefix != prefix:
        return redirect(url_for(endpoint, prefix=norm_prefix))
    return norm_prefix


def _search(manager_, q: str) -> List[str]:
    q_norm = q.lower()
    return [prefix for prefix in manager_.registry if q_norm in prefix]


def _autocomplete(manager_, q: str) -> Mapping[str, Any]:
    r"""Run the autocomplete algorithm.

    :param manager_: A manager
    :param q: The query string
    :return: A dictionary with the autocomplete results.

    Before completion is of prefix:

    >>> from bioregistry import manager
    >>> _autocomplete(manager, 'cheb')
    {'query': 'cheb', 'results': ['chebi'], 'success': True, 'reason': 'searched prefix', 'url': None}

    If only prefix is complete:

    >>> _autocomplete(manager, 'chebi')
    {'query': 'chebi', 'results': ['chebi'], 'success': True, 'reason': 'matched prefix', 'url': 'https://bioregistry.io/chebi'}

    Not matching the pattern:

    >>> _autocomplete(manager, 'chebi:NOPE')
    {'query': 'chebi:NOPE', 'prefix': 'chebi', 'pattern': '^\\d+$', 'identifier': 'NOPE', 'success': False, 'reason': 'failed validation', 'url': None}

    Matching the pattern:

    >>> _autocomplete(manager, 'chebi:1234')
    {'query': 'chebi:1234', 'prefix': 'chebi', 'pattern': '^\\d+$', 'identifier': '1234', 'success': True, 'reason': 'passed validation', 'url': 'https://bioregistry.io/chebi:1234'}
    """  # noqa: E501
    if ":" not in q:
        url: Optional[str]
        if q in manager_.registry:
            reason = "matched prefix"
            url = f"{BIOREGISTRY_REMOTE_URL.rstrip()}/{q}"
        else:
            reason = "searched prefix"
            url = None
        return dict(
            query=q,
            results=_search(manager_, q),
            success=True,
            reason=reason,
            url=url,
        )
    prefix, identifier = q.split(":", 1)
    norm_prefix = manager_.normalize_prefix(prefix)
    if norm_prefix is None:
        return dict(
            query=q,
            prefix=prefix,
            identifier=identifier,
            success=False,
            reason="bad prefix",
        )
    pattern = manager_.get_pattern(prefix)
    if pattern is None:
        success = True
        reason = "no pattern"
        url = manager_.get_bioregistry_iri(prefix, identifier)
    elif manager_.is_standardizable_identifier(prefix, identifier):
        success = True
        reason = "passed validation"
        url = manager_.get_bioregistry_iri(prefix, identifier)
    else:
        success = False
        reason = "failed validation"
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
    if not manager.is_standardizable_identifier(prefix, identifier):
        return abort(
            404,
            f"invalid identifier: {curie_to_str(prefix, identifier)} for pattern {manager.get_pattern(prefix)}",
        )
    providers = manager.get_providers(prefix, identifier)
    if not providers:
        return abort(404, f"no providers available for {curie_to_str(prefix, identifier)}")

    return dict(
        query=dict(prefix=prefix, identifier=identifier),
        providers=providers,
    )


def jsonify(data):
    """Dump data as JSON, like like :func:`flask.jsonify`."""
    return current_app.response_class(
        json.dumps(data, ensure_ascii=False, default=extended_encoder) + "\n",
        mimetype=current_app.config["JSONIFY_MIMETYPE"],
    )


def yamlify(data):
    """Dump data as YAML, like :func:`flask.jsonify`."""
    if isinstance(data, BaseModel):
        data = sanitize_model(data)

    return current_app.response_class(
        yaml.safe_dump(data=data),
        mimetype="text/plain",
    )


def _get_format(default: str = "json") -> str:
    return request.args.get("format", default=default)


def serialize(data, serializers: Optional[Sequence[Tuple[str, str, Callable]]] = None):
    """Serialize either as JSON or YAML."""
    fmt = _get_format()
    if fmt == "json":
        return jsonify(data)
    elif fmt in {"yaml", "yml"}:
        return yamlify(data)
    for name, mimetype, func in serializers or []:
        if fmt == name:
            return current_app.response_class(func(data), mimetype=mimetype)
    return abort(404, f"invalid format: {fmt}")
