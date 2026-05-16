"""UI endpoint for the resolver."""

from __future__ import annotations

import curies
import flask
import werkzeug
from flask import Response, redirect, render_template, request, url_for

from .base import ui_blueprint
from .resource import resource as resource_route
from ..constants import MIMETYPE_TO_RDFLIB_FORMAT
from ..proxies import manager
from ..utils import (
    IdentifierResponse,
    ResponseWrapperError,
    flask_jsonify_pydantic,
    flask_response_rdf,
    flask_yamlify_pydantic,
    get_accept_media_type,
    get_provider_graph,
)
from ...schema.struct import Resource

__all__ = ["resolve"]


#: this is a hack to make it work when the LUID starts with a slash for
#: ARK, since ARK doesn't actually require a slash. Will break
#: if there are other LUIDs that actually require a slash in front
ark_hacked_route = ui_blueprint.route("/<prefix>:/<path:identifier>")


@ui_blueprint.route("/<prefix>")
@ui_blueprint.route("/<prefix>:<path:identifier>")
@ark_hacked_route
def resolve(
    prefix: str, identifier: str | None = None
) -> str | werkzeug.Response | tuple[str | werkzeug.Response, int]:
    """Resolve a CURIE.

    The following things can make a CURIE unable to resolve:

    1. The prefix is not registered
    2. The prefix has a validation pattern and the identifier does not match it
    3. There are no providers available for the URL
    """
    try:
        resource, reference = _clean_reference(prefix, identifier)
    except ResponseWrapperError as rw:
        return rw.get_value()

    identifier = reference.identifier

    accept = get_accept_media_type()
    provider = request.args.get("provider")
    if accept != "text/html":
        if provider:
            flask.abort(400, f"can't use `provider` query parameter with request for {accept}")

        providers = manager.get_providers(resource.prefix, reference.identifier)
        if not providers:
            raise flask.abort(404, f"no providers available for {reference.curie}")

        if accept in MIMETYPE_TO_RDFLIB_FORMAT:
            graph = get_provider_graph(manager, reference, providers)
            return flask_response_rdf(graph, mimetype=accept)
        elif accept == "application/json":
            return flask_jsonify_pydantic(IdentifierResponse(query=reference, providers=providers))
        elif accept == "application/yaml":
            return flask_yamlify_pydantic(IdentifierResponse(query=reference, providers=providers))
        else:
            raise flask.abort(404, f"invalid accept type: {accept}")

    url = manager.get_iri(
        resource.prefix, reference.identifier, use_bioregistry_io=False, provider=provider
    )
    if not url:
        return Response(
            render_template(
                "resolve_errors/missing_providers.html",
                prefix=reference.prefix,
                identifier=reference.identifier,
            ),
            status=404,
        )
    try:
        # TODO remove any garbage characters?
        return redirect(url)
    except ValueError:  # headers could not be constructed
        return Response(
            render_template(
                "resolve_errors/disallowed_identifier.html",
                prefix=resource.prefix,
                identifier=identifier,
            ),
            status=404,
        )


def _clean_reference(
    prefix: str, identifier: str | None = None
) -> tuple[Resource, curies.Reference]:
    if ":" in prefix:
        # A colon might appear in the prefix if there are multiple colons
        # in the CURIE, since Flask/Werkzeug parses from right to left.
        # This block reorganizes the parts of the CURIE based on that assumption
        prefix, middle = prefix.split(":", 1)
        if identifier:
            identifier = f"{middle}:{identifier}"
        else:
            identifier = middle  # not sure how this could happen, though

    resource = manager.get_resource(prefix)
    if resource is None:
        raise ResponseWrapperError(
            render_template(
                "resolve_errors/missing_prefix.html", prefix=prefix, identifier=identifier
            ),
            404,
        )
    if identifier is None:
        raise ResponseWrapperError(
            redirect(url_for("." + resource_route.__name__, prefix=resource.prefix))
        )

    # TODO consolidate with logic inside bioregistry.NormalizedReference

    identifier = resource.standardize_identifier(identifier)
    pattern = resource.get_pattern()
    if pattern and not resource.is_valid_identifier(identifier):
        raise ResponseWrapperError(
            render_template(
                "resolve_errors/invalid_identifier.html",
                prefix=prefix,
                identifier=identifier,
                pattern=pattern,
            ),
            404,
        )

    return resource, curies.Reference(prefix=resource.prefix, identifier=identifier)
