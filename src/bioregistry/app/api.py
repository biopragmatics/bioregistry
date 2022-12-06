# -*- coding: utf-8 -*-

"""API blueprint and routes."""

from functools import partial

from flask import Blueprint, abort, jsonify, request

from .proxies import manager
from .utils import (
    _autocomplete,
    _get_identifier,
    _normalize_prefix_or_404,
    _search,
    serialize,
)
from ..export.rdf_export import (
    collection_to_rdf_str,
    metaresource_to_rdf_str,
    resource_to_rdf_str,
)
from ..schema import Collection, sanitize_mapping
from ..schema_utils import (
    read_collections_contributions,
    read_prefix_contacts,
    read_prefix_contributions,
    read_prefix_reviews,
    read_registry_contributions,
)

__all__ = [
    "api_blueprint",
]

api_blueprint = Blueprint("metaregistry_api", __name__, url_prefix="/api")


@api_blueprint.route("/registry")
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
    return serialize(sanitize_mapping(manager.registry))


@api_blueprint.route("/registry/<prefix>")
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
        enum: [json, yaml, turtle, jsonld]
    """  # noqa:DAR101,DAR201
    prefix = _normalize_prefix_or_404(prefix)
    if not isinstance(prefix, str):
        return jsonify(query=prefix, message="Invalid prefix"), 404
    resource = manager.get_resource(prefix)
    assert resource is not None
    return _serialize_resource(resource)


@api_blueprint.route("/metaregistry/<metaprefix>/<metaidentifier>")
def resource_from_metaregistry(metaprefix: str, metaidentifier: str):
    """Get a resource by an external prefix.

    ---
    tags:
    - resource
    parameters:
    - name: metaprefix
      in: path
      description: The meteprefix for a registry
      required: true
      type: string
      example: obofoundry
    - name: metaidentifier
      in: path
      description: The prefix instide for a registry
      required: true
      type: string
      example: GO
    - name: format
      description: The file type
      in: query
      required: false
      default: json
      schema:
        type: string
        enum: [json, yaml, turtle, jsonld]

    """  # noqa:DAR101,DAR201
    if metaprefix not in manager.metaregistry:
        return abort(404, f"invalid metaprefix: {metaprefix}")
    prefix = manager.lookup_from(metaprefix, metaidentifier, normalize=True)
    if not prefix:
        return abort(404, f"invalid metaidentifier: {metaidentifier}")
    resource = manager.get_resource(prefix)
    assert resource is not None
    return _serialize_resource(resource, rasterize=True)


def _serialize_resource(resource, rasterize: bool = False):
    if rasterize:
        resource = manager.rasterized_resource(resource.prefix, resource)
    data = dict(prefix=resource.prefix, **resource.dict(exclude_unset=True, exclude_none=True))
    return serialize(
        data,
        serializers=[
            ("turtle", "text/plain", partial(resource_to_rdf_str, manager=manager, fmt="turtle")),
            (
                "jsonld",
                "application/ld+json",
                partial(resource_to_rdf_str, manager=manager, fmt="json-ld"),
            ),
        ],
    )


@api_blueprint.route("/metaregistry")
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
    return serialize(sanitize_mapping(manager.metaregistry))


@api_blueprint.route("/metaregistry/<metaprefix>")
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
        enum: [json, yaml, turtle, jsonld]
    """  # noqa:DAR101,DAR201
    data = manager.metaregistry.get(metaprefix)
    if not data:
        abort(404, f"Invalid metaprefix: {metaprefix}")
    return serialize(
        data,
        serializers=[
            (
                "turtle",
                "text/plain",
                partial(metaresource_to_rdf_str, manager=manager, fmt="turtle"),
            ),
            (
                "jsonld",
                "application/ld+json",
                partial(metaresource_to_rdf_str, manager=manager, fmt="json-ld"),
            ),
        ],
    )


@api_blueprint.route("/collections")
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
    return serialize(sanitize_mapping(manager.collections))


@api_blueprint.route("/collection/<identifier>")
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
        enum: [json, yaml, context, turtle, jsonld]
    """  # noqa:DAR101,DAR201
    data = manager.collections.get(identifier)
    if not data:
        abort(404, f"Invalid collection: {identifier}")
    return serialize(
        data,
        serializers=[
            ("context", "application/ld+json", Collection.as_context_jsonld_str),
            ("turtle", "text/plain", partial(collection_to_rdf_str, manager=manager, fmt="turtle")),
            (
                "jsonld",
                "application/ld+json",
                partial(collection_to_rdf_str, manager=manager, fmt="json-ld"),
            ),
        ],
    )


@api_blueprint.route("/contexts")
def contexts():
    """Get all contexts.

    ---
    tags:
    - context
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
    return serialize(sanitize_mapping(manager.contexts))


@api_blueprint.route("/context/<identifier>")
def context(identifier: str):
    """Get a context.

    ---
    tags:
    - context
    parameters:
    - name: identifier
      in: path
      description: The identifier of the context
      required: true
      type: string
      example: obo
    - name: format
      description: The file type
      in: query
      required: false
      default: json
      schema:
        type: string
        enum: [json, yaml]
    """  # noqa:DAR101,DAR201
    data = manager.contexts.get(identifier)
    if not data:
        abort(404, f"Invalid context: {identifier}")
    return serialize(data)


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


@api_blueprint.route("/contributors")
def contributors():
    """Get all contributors.

    ---
    tags:
    - contributor
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
    return serialize(sanitize_mapping(manager.read_contributors()))


@api_blueprint.route("/contributor/<orcid>")
def contributor(orcid: str):
    """Get a contributor.

    ---
    tags:
    - contributor
    parameters:
    - name: orcid
      in: path
      description: The ORCID identifier of the contributor
      required: true
      type: string
      example: 0000-0002-8424-0604
    - name: format
      description: The file type
      in: query
      required: false
      default: json
      schema:
        type: string
        enum: [json, yaml]
    """  # noqa:DAR101,DAR201
    author = manager.read_contributors().get(orcid)
    if author is None:
        return abort(404, f"No contributor with orcid:{orcid}")

    return serialize(
        {
            **author.dict(),
            "prefix_contributions": sorted(
                read_prefix_contributions(manager.registry).get(orcid, [])
            ),
            "prefix_reviews": sorted(read_prefix_reviews(manager.registry).get(orcid, [])),
            "prefix_contacts": sorted(read_prefix_contacts(manager.registry).get(orcid, [])),
            "registries": sorted(read_registry_contributions(manager.metaregistry).get(orcid, [])),
            "collections": sorted(
                read_collections_contributions(manager.collections).get(orcid, [])
            ),
        }
    )


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


@api_blueprint.route("/external/mapping/<source>/<target>")
def mapping(source: str, target: str):
    """Get mappings between two external prefixes.

    ---
    parameters:
    - name: source
      in: path
      description: The source metaprefix (e.g., obofoundry)
      required: true
      type: string
    - name: target
      in: path
      description: The target metaprefix (e.g., bioportal)
      required: true
      type: string
    """  # noqa:DAR101,DAR201
    if source not in manager.metaregistry:
        return {"bad source prefix": source}, 400
    if target not in manager.metaregistry:
        return {"bad target prefix": target}, 400
    rv = {}
    source_only = set()
    target_only = set()
    for resource in manager.registry.values():
        mappings = resource.get_mappings()
        mp1_prefix = mappings.get(source)
        mp2_prefix = mappings.get(target)
        if mp1_prefix and mp2_prefix:
            rv[mp1_prefix] = mp2_prefix
        elif mp1_prefix and not mp2_prefix:
            source_only.add(mp1_prefix)
        elif not mp1_prefix and mp2_prefix:
            target_only.add(mp2_prefix)

    return jsonify(
        meta=dict(
            len_overlap=len(rv),
            source=source,
            target=target,
            len_source_only=len(source_only),
            len_target_only=len(target_only),
            source_only=sorted(source_only),
            target_only=sorted(target_only),
        ),
        mappings=rv,
    )
