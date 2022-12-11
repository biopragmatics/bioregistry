# -*- coding: utf-8 -*-

"""API blueprint and routes."""

from flask import Blueprint, abort, jsonify, request

from .proxies import manager
from .utils import (
    _autocomplete,
    _get_identifier,
    _search,
    serialize,
)

__all__ = [
    "api_blueprint",
]

api_blueprint = Blueprint("metaregistry_api", __name__, url_prefix="/api")


@api_blueprint.route("/reference/<prefix>:<identifier>")
def reference(prefix: str, identifier: str):
    """Look up information on the reference.

    ---
    tags:
    - reference
    parameters:
    - name: prefix
      in: path
      description: The prefix for the entry
      required: true
      type: string
      example: efo
    - name: identifier
      in: path
      description: The identifier for the entry
      required: true
      type: string
      example: 0000311
    - name: format
      description: The file type
      in: query
      required: false
      default: json
      schema:
        type: string
        enum: [json, yaml]
    """  # noqa:DAR101,DAR201
    return serialize(_get_identifier(prefix, identifier))


@api_blueprint.route("/search")
def search():
    """Search for a prefix.

    ---
    parameters:
    - name: q
      in: query
      description: The prefix for the entry
      required: true
      type: string
    """  # noqa:DAR101,DAR201
    q = request.args.get("q")
    if q is None:
        abort(400)
    return jsonify(_search(manager, q))


@api_blueprint.route("/autocomplete")
def autocomplete():
    """Complete a resolution query.

    ---
    parameters:
    - name: q
      in: query
      description: The prefix for the entry
      required: true
      type: string
    """  # noqa:DAR101,DAR201
    q = request.args.get("q")
    if q is None:
        abort(400)
    return jsonify(_autocomplete(manager, q))


@api_blueprint.route("/context.jsonld")
def generate_context_json_ld():
    """Generate an *ad-hoc* context JSON-LD file from the given parameters.

    You can either give prefixes as a comma-separated list like:

    https://bioregistry.io/api/context.jsonld?prefix=go,doid,oa

    or you can use multiple entries for "prefix" like:

    https://bioregistry.io/api/context.jsonld?prefix=go&prefix=doid&prefix=oa
    ---
    parameters:
    - name: prefix
      in: query
      description: The prefix for the entry. Can be given multiple.
      required: true
      type: string
    """  # noqa:DAR101,DAR201
    prefix_map = {}
    for arg in request.args.getlist("prefix", type=str):
        for prefix in arg.split(","):
            prefix = manager.normalize_prefix(prefix.strip())
            if prefix is None:
                continue
            uri_prefix = manager.get_uri_prefix(prefix)
            if uri_prefix is None:
                continue
            prefix_map[prefix] = uri_prefix

    return jsonify(
        {
            "@context": prefix_map,
        }
    )
