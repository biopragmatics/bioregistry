# -*- coding: utf-8 -*-

"""Utility functions for the Bioregistry :mod:`flask` app."""

import json
from typing import Any, Callable, Dict, List, Mapping, Optional, Sequence, Tuple

import yaml
from flask import abort, current_app, redirect, render_template, request, url_for
from pydantic import BaseModel

from bioregistry.resource_manager import Manager
from bioregistry.schema import Resource, sanitize_model
from bioregistry.utils import curie_to_str, extended_encoder

from .proxies import manager
from ..utils import _norm


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


def _search(manager_: Manager, q: str) -> List[Tuple[str, str]]:
    q_norm = _norm(q)
    results = [
        (prefix, lookup if _norm(prefix) != lookup else "")
        for lookup, prefix in manager_.synonyms.items()
        if q_norm in lookup
    ]
    return sorted(results)


def _autocomplete(manager_: Manager, q: str, url_prefix: Optional[str] = None) -> Mapping[str, Any]:
    r"""Run the autocomplete algorithm.

    :param manager_: A manager
    :param q: The query string
    :param url_prefix:
        The explicit URL prefix. If not used, relative paths are generated. Introduced to
        solve https://github.com/biopragmatics/bioregistry/issues/596.
    :return: A dictionary with the autocomplete results.

    Before completion is of prefix:

    >>> from bioregistry import manager
    >>> _autocomplete(manager, 'cheb')
    {'query': 'cheb', 'results': [('chebi', ''), ('chebi', 'chebiid'), ('goche', 'gochebi')], 'success': True, 'reason': 'searched prefix', 'url': None}

    If only prefix is complete:

    >>> _autocomplete(manager, 'chebi')
    {'query': 'chebi', 'results': [('chebi', ''), ('chebi', 'chebiid'), ('goche', 'gochebi')], 'success': True, 'reason': 'matched prefix', 'url': '/chebi'}

    Not matching the pattern:

    >>> _autocomplete(manager, 'chebi:NOPE')
    {'query': 'chebi:NOPE', 'prefix': 'chebi', 'pattern': '^\\d+$', 'identifier': 'NOPE', 'success': False, 'reason': 'failed validation', 'url': None}

    Matching the pattern:

    >>> _autocomplete(manager, 'chebi:1234')
    {'query': 'chebi:1234', 'prefix': 'chebi', 'pattern': '^\\d+$', 'identifier': '1234', 'success': True, 'reason': 'passed validation', 'url': '/chebi:1234'}
    """  # noqa: E501
    if url_prefix is None:
        url_prefix = ""
    url_prefix = url_prefix.rstrip().rstrip("/")

    if ":" not in q:
        url: Optional[str]
        if q in manager_.registry:
            reason = "matched prefix"
            url = f"{url_prefix}/{q}"
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
    resource = manager_.get_resource(prefix)
    if resource is None:
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
        norm_id = resource.standardize_identifier(identifier)
        url = f"{url_prefix}/{resource.get_curie(norm_id)}"
    elif resource.is_standardizable_identifier(identifier):
        success = True
        reason = "passed validation"
        norm_id = resource.standardize_identifier(identifier)
        url = f"{url_prefix}/{resource.get_curie(norm_id)}"
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
        json.dumps(data, ensure_ascii=False, default=extended_encoder),
        mimetype="application/json",
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
