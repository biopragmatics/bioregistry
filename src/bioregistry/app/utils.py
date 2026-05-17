"""Utility functions for the :mod:`flask` app."""

from __future__ import annotations

import json
from collections.abc import Callable, Mapping, Sequence
from functools import partial
from typing import Any, TypeAlias, cast

import curies
import rdflib
import werkzeug
import yaml
from curies import Reference
from flask import Response, abort, current_app, redirect, render_template, request, url_for
from pydantic import BaseModel
from rdflib import RDFS

from .constants import KEY_TO_MIMETYPE, MIMETYPE_TO_RDFLIB_FORMAT
from .proxies import manager
from ..resource_manager import Manager
from ..utils import _norm


def _get_resource_providers(
    prefix: str, identifier: str | None
) -> list[dict[str, str | None]] | None:
    if identifier is None:
        return None
    rv: list[dict[str, str | None]] = []
    for metaprefix, uri in manager.get_providers_list(
        prefix, identifier, filter_known_inactive=True
    ):
        name: str | None
        homepage: str | None
        if metaprefix == "default":
            metaprefix = prefix
            name = manager.get_name(prefix, strict=True)
            homepage = manager.get_homepage(prefix, strict=True)
        elif metaprefix == "rdf":
            name = f"{manager.get_name(prefix, strict=True)} (RDF)"
            homepage = manager.get_homepage(prefix, strict=True)
        else:
            name = manager.get_registry_name(metaprefix, strict=False)
            homepage = manager.get_registry_homepage(metaprefix, strict=False)
        rv.append(
            {
                "metaprefix": metaprefix,
                "homepage": homepage,
                "name": name,
                "uri": uri,
            }
        )
    return rv


def _normalize_prefix_or_404(
    prefix: str, endpoint: str | None = None
) -> str | werkzeug.Response | tuple[str, int]:
    try:
        norm_prefix = manager.normalize_prefix(prefix)
    except ValueError:
        norm_prefix = None
    if norm_prefix is None:
        return render_template("resolve_errors/missing_prefix.html", prefix=prefix), 404
    elif endpoint is not None and norm_prefix != prefix:
        return redirect(url_for(endpoint, prefix=norm_prefix))
    return norm_prefix


def _search(manager_: Manager, q: str) -> list[tuple[str, str]]:
    q_norm = _norm(q)
    results = [
        (prefix, lookup if _norm(prefix) != lookup else "")
        for lookup, prefix in manager_.synonyms.items()
        if q_norm in lookup
    ]
    return sorted(results)


def _autocomplete(manager_: Manager, q: str, url_prefix: str | None = None) -> Mapping[str, Any]:
    r"""Run the autocomplete algorithm.

    :param manager_: A manager
    :param q: The query string
    :param url_prefix:
        The explicit URL prefix. If not used, relative paths are generated. Introduced to
        solve https://github.com/biopragmatics/bioregistry/issues/596.
    :return: A dictionary with the autocomplete results.

    Before completion is of prefix:

    >>> from bioregistry import manager
    >>> _autocomplete(manager, "cheb")
    {'query': 'cheb', 'results': [('chebi', ''), ('chebi', 'chebiid'), ('goche', 'gochebi')], 'success': True, 'reason': 'searched prefix', 'url': None}

    If only prefix is complete:

    >>> _autocomplete(manager, "chebi")
    {'query': 'chebi', 'results': [('chebi', ''), ('chebi', 'chebiid'), ('goche', 'gochebi')], 'success': True, 'reason': 'matched prefix', 'url': '/chebi'}

    Not matching the pattern:

    >>> _autocomplete(manager, "chebi:NOPE")
    {'query': 'chebi:NOPE', 'prefix': 'chebi', 'pattern': '^\\d+$', 'identifier': 'NOPE', 'success': False, 'reason': 'failed validation', 'url': None}

    Matching the pattern:

    >>> _autocomplete(manager, "chebi:1234")
    {'query': 'chebi:1234', 'prefix': 'chebi', 'pattern': '^\\d+$', 'identifier': '1234', 'success': True, 'reason': 'passed validation', 'url': '/chebi:1234'}
    """
    if url_prefix is None:
        url_prefix = ""
    url_prefix = url_prefix.rstrip().rstrip("/")

    if ":" not in q:
        url: str | None
        if q in manager_.registry:
            reason = "matched prefix"
            url = f"{url_prefix}/{q}"
        else:
            reason = "searched prefix"
            url = None
        return {
            "query": q,
            "results": _search(manager_, q),
            "success": True,
            "reason": reason,
            "url": url,
        }
    prefix, identifier = q.split(":", 1)
    resource = manager_.get_resource(prefix)
    if resource is None:
        return {
            "query": q,
            "prefix": prefix,
            "identifier": identifier,
            "success": False,
            "reason": "bad prefix",
        }
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
    return {
        "query": q,
        "prefix": prefix,
        "pattern": pattern,
        "identifier": identifier,
        "success": success,
        "reason": reason,
        "url": url,
    }


Serializer: TypeAlias = Callable[[BaseModel], str]


def serialize(
    model: BaseModel,
    serializers: Sequence[tuple[str, str, Serializer]] | None = None,
    negotiate: bool = False,
) -> Response:
    """Serialize either as JSON or YAML."""
    if negotiate:
        accept = get_accept_media_type()
    else:
        arg = request.args.get("format", "json")
        if arg not in KEY_TO_MIMETYPE:
            return abort(
                400, f"unhandled value for `format`: {arg}. Use one of: {sorted(KEY_TO_MIMETYPE)}"
            )
        accept = KEY_TO_MIMETYPE[arg]

    if accept == "application/json":
        return flask_jsonify_pydantic(model)
    elif accept in "application/yaml":
        return flask_yamlify_pydantic(model)
    for _name, mimetype, func in serializers or []:
        if accept == mimetype:
            return cast(Response, current_app.response_class(func(model), mimetype=mimetype))
    return abort(404, f"unhandled media type: {accept}")


def flask_jsonify_pydantic(model: BaseModel) -> Response:
    """Serialize a model to JSON."""
    # do this instead of flask.jsonify to ensure_ascii=False
    return cast(
        Response,
        current_app.response_class(
            json.dumps(model.model_dump(exclude_unset=True, exclude_none=True), ensure_ascii=False),
            mimetype="application/json",
        ),
    )


def flask_yamlify_pydantic(model: BaseModel) -> Response:
    """Serialize a model to YAML."""
    return yamlify(model.model_dump(exclude_unset=True, exclude_none=True))


def flask_response_rdf(graph: rdflib.Graph, mimetype: str) -> Response:
    """Serialize a graph to RDF."""
    return cast(
        Response,
        current_app.response_class(
            graph.serialize(format=MIMETYPE_TO_RDFLIB_FORMAT[mimetype]), mimetype=mimetype
        ),
    )


def yamlify(data: Any) -> Response:
    """Create a YAML response."""
    return cast(
        Response,
        current_app.response_class(
            yaml.safe_dump(data, allow_unicode=True), mimetype="application/yaml"
        ),
    )


def serialize_model(entry: BaseModel, func, negotiate: bool = False) -> Response:  # type:ignore
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
        if fmt not in KEY_TO_MIMETYPE:
            raise abort(
                400, f"bad query parameter format={fmt}. Should be one of {list(KEY_TO_MIMETYPE)}"
            )
        return KEY_TO_MIMETYPE[fmt]

    # TODO could try and raise on "bad" mimetypes, but this
    #  might be more of a rabbit hole for parsing all sorts of extra parts too

    # If accept is specifically set to one of the special quanties, then use it.
    accept = str(request.accept_mimetypes)
    if accept in KEY_TO_MIMETYPE.values():
        return accept

    # Otherwise, return HTML
    return "text/html"


def get_provider_graph(
    manager: Manager, reference: curies.Reference, providers: dict[str, str]
) -> rdflib.Graph:
    """Get the provider graph."""
    graph = rdflib.Graph()
    node_str = f"{manager.base_url}/{reference.curie}"
    node = rdflib.URIRef(node_str)
    for _key, provider in providers.items():
        if provider != node_str:
            graph.add((node, RDFS.seeAlso, rdflib.URIRef(provider)))
    return graph


class ResponseWrapperError(ValueError):
    """An exception that helps with code reuse that returns multiple value types."""

    def __init__(self, response: str | werkzeug.Response, code: int | None = None) -> None:
        """Instantiate this "exception", which is a tricky way of writing a macro."""
        self.response = response
        self.code = code

    def get_value(self) -> tuple[str | werkzeug.Response, int] | str | werkzeug.Response:
        """Get either the response, or a pair of response + code if a code is available."""
        if self.code is not None:
            return self.response, self.code
        return self.response


class IdentifierResponse(BaseModel):
    """A response for looking up a reference."""

    query: Reference
    providers: Mapping[str, str]
