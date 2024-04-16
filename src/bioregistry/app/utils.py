# -*- coding: utf-8 -*-

"""Utility functions for the Bioregistry :mod:`flask` app."""

import json
from functools import partial
from typing import Any, Callable, Dict, List, Mapping, Optional, Sequence, Tuple

import yaml
from flask import (
    Response,
    abort,
    current_app,
    redirect,
    render_template,
    request,
    url_for,
)
from pydantic import BaseModel

from bioregistry.resource_manager import Manager

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
        elif metaprefix == "rdf":
            name = f"{manager.get_name(prefix)} (RDF)"
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


def serialize(
    data: BaseModel,
    serializers: Optional[Sequence[Tuple[str, str, Callable]]] = None,
    negotiate: bool = False,
) -> Response:
    """Serialize either as JSON or YAML."""
    if negotiate:
        accept = get_accept_media_type()
    else:
        arg = request.args.get("format", "json")
        if arg not in FORMAT_MAP:
            return abort(
                400, f"unhandled value for `format`: {arg}. Use one of: {sorted(FORMAT_MAP)}"
            )
        accept = FORMAT_MAP[arg]

    if accept == "application/json":
        return current_app.response_class(
            json.dumps(data.dict(exclude_unset=True, exclude_none=True), ensure_ascii=False),
            mimetype="application/json",
        )
    elif accept in "application/yaml":
        return current_app.response_class(
            yaml.safe_dump(data.dict(exclude_unset=True, exclude_none=True), allow_unicode=True),
            mimetype="text/plain",
        )
    for _name, mimetype, func in serializers or []:
        if accept == mimetype:
            return current_app.response_class(func(data), mimetype=mimetype)
    return abort(404, f"unhandled media type: {accept}")


def serialize_model(entry: BaseModel, func, negotiate: bool = False) -> Response:
    """Serialize a model."""
    return serialize(
        entry,
        negotiate=negotiate,
        serializers=[
            ("turtle", "text/turtle", partial(func, manager=manager, fmt="turtle")),
            ("n3", "text/n3", partial(func, manager=manager, fmt="n3")),
            ("rdf", "application/rdf+xml", partial(func, manager=manager, fmt="xml")),
            (
                "jsonld",
                "application/ld+json",
                partial(func, manager=manager, fmt="json-ld"),
            ),
        ],
    )


def get_accept_media_type() -> str:
    """Get accept type."""
    fmt = request.args.get("format")
    if fmt is not None:
        rv = FORMAT_MAP.get(fmt)
        if rv:
            return rv
        return abort(400, f"bad query parameter format={fmt}. Should be one of {list(FORMAT_MAP)}")

    # If accept is specifically set to one of the special quanties, then use it.
    accept = str(request.accept_mimetypes)
    if accept in FORMAT_MAP.values():
        return accept

    # Otherwise, return HTML
    return "text/html"


FORMAT_MAP = {
    "json": "application/json",
    "yml": "application/yaml",
    "yaml": "application/yaml",
    "turtle": "text/turtle",
    "jsonld": "application/ld+json",
    "json-ld": "application/ld+json",
    "rdf": "application/rdf+xml",
    "n3": "text/n3",
}
