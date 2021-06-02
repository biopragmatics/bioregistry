# -*- coding: utf-8 -*-

"""API blueprint and routes."""

from flask import Blueprint, abort, jsonify, request

import bioregistry
from .utils import _autocomplete, _get_identifier, _normalize_prefix_or_404, _search, serialize

api_blueprint = Blueprint('api', __name__, url_prefix='/api')


@api_blueprint.route('/registry')
def resources():
    """Get all resources.

    ---
    tags:
    - resource
    parameters:
    - name: format
      description: The file type
      in: query
      required: false
      default: json
      schema:
        type: string
        enum: [json, yaml]
    """  # noqa:DAR101,DAR201
    return serialize(bioregistry.read_registry())


@api_blueprint.route('/registry/<prefix>')
def resource(prefix: str):
    """Get a resource.

    ---
    tags:
    - resource
    parameters:
    - name: prefix
      in: path
      description: The prefix for the entry
      required: true
      type: string
      example: doid
    - name: format
      description: The file type
      in: query
      required: false
      default: json
      schema:
        type: string
        enum: [json, yaml]
    """  # noqa:DAR101,DAR201
    prefix = _normalize_prefix_or_404(prefix)
    return serialize(prefix=prefix, **bioregistry.get(prefix))  # type: ignore


@api_blueprint.route('/metaregistry')
def metaresources():
    """Get all metaresources.

    ---
    tags:
    - metaresource
    parameters:
    - name: format
      description: The file type
      in: query
      required: false
      default: json
      schema:
        type: string
        enum: [json, yaml]
    """  # noqa:DAR101,DAR201
    return serialize(bioregistry.read_metaregistry())


@api_blueprint.route('/metaregistry/<metaprefix>')
def metaresource(metaprefix: str):
    """Get a metaresource.

    ---
    tags:
    - metaresource
    parameters:
    - name: prefix
      in: path
      description: The prefix for the metaresource
      required: true
      type: string
      example: doid
    - name: format
      description: The file type
      in: query
      required: false
      default: json
      schema:
        type: string
        enum: [json, yaml]
    """  # noqa:DAR101,DAR201
    data = bioregistry.get_registry(metaprefix)
    if not data:
        abort(404, f'Invalid metaprefix: {metaprefix}')
    return serialize(data)


@api_blueprint.route('/collections')
def collections():
    """Get all collections.

    ---
    tags:
    - collection
    parameters:
    - name: format
      description: The file type
      in: query
      required: false
      default: json
      schema:
        type: string
        enum: [json, yaml]
    """  # noqa:DAR101,DAR201
    return serialize(bioregistry.read_collections())


@api_blueprint.route('/collection/<identifier>')
def collection(identifier: str):
    """Get a collection.

    ---
    tags:
    - collection
    parameters:
    - name: prefix
      in: path
      description: The identifier of the collection
      required: true
      type: string
      example: 0000001
    - name: format
      description: The file type
      in: query
      required: false
      default: json
      schema:
        type: string
        enum: [json, yaml]
    """  # noqa:DAR101,DAR201
    data = bioregistry.get_collection(identifier)
    if not data:
        abort(404, f'Invalid collection: {identifier}')
    return serialize(data)


@api_blueprint.route('/reference/<prefix>:<identifier>')
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


@api_blueprint.route('/search')
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
    q = request.args.get('q')
    if q is None:
        abort(400)
    return jsonify(_search(q))


@api_blueprint.route('/autocomplete')
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
    q = request.args.get('q')
    if q is None:
        abort(400)
    return jsonify(_autocomplete(q))
