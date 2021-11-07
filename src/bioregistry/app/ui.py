# -*- coding: utf-8 -*-

"""User blueprint for the bioregistry web application."""

from typing import Optional

from flask import Blueprint, abort, redirect, render_template, url_for

import bioregistry

from .utils import (
    _get_resource_mapping_rows,
    _get_resource_providers,
    _normalize_prefix_or_404,
)
from ..utils import (
    curie_to_str,
    read_collections_contributions,
    read_prefix_contributions,
    read_prefix_reviews,
)

__all__ = [
    "ui_blueprint",
]

ui_blueprint = Blueprint("ui", __name__)

FORMATS = [
    ("JSON", "json"),
    ("YAML", "yaml"),
]


@ui_blueprint.route("/registry/")
def resources():
    """Serve the Bioregistry page."""
    return render_template(
        "resources.html",
        formats=FORMATS,
        registry=bioregistry.read_registry(),
    )


@ui_blueprint.route("/metaregistry/")
def metaresources():
    """Serve the Bioregistry metaregistry page."""
    return render_template(
        "metaresources.html",
        rows=bioregistry.read_metaregistry().values(),
        formats=FORMATS,
    )


@ui_blueprint.route("/collection/")
def collections():
    """Serve the Bioregistry collection page."""
    return render_template(
        "collections.html",
        rows=bioregistry.read_collections().items(),
        formats=FORMATS,
    )


@ui_blueprint.route("/registry/<prefix>")
def resource(prefix: str):
    """Serve the a Bioregistry entry page."""
    prefix = _normalize_prefix_or_404(prefix, "." + resource.__name__)
    if not isinstance(prefix, str):
        return prefix
    _resource = bioregistry.get_resource(prefix)
    if _resource is None:
        raise RuntimeError
    example = _resource.get_example()
    # TODO move into manager
    example_curie = (
        curie_to_str(_resource.get_preferred_prefix() or prefix, example) if example else None
    )
    return render_template(
        "resource.html",
        prefix=prefix,
        resource=_resource,
        name=bioregistry.get_name(prefix),
        example=example,
        example_curie=example_curie,
        mappings=_get_resource_mapping_rows(_resource),
        synonyms=bioregistry.get_synonyms(prefix),
        homepage=bioregistry.get_homepage(prefix),
        pattern=bioregistry.get_pattern(prefix),
        curie_pattern=bioregistry.get_curie_pattern(prefix),
        version=bioregistry.get_version(prefix),
        has_no_terms=bioregistry.has_no_terms(prefix),
        obo_download=bioregistry.get_obo_download(prefix),
        owl_download=bioregistry.get_owl_download(prefix),
        json_download=bioregistry.get_json_download(prefix),
        namespace_in_lui=bioregistry.get_namespace_in_lui(prefix),
        deprecated=bioregistry.is_deprecated(prefix),
        contact=bioregistry.get_contact(prefix),
        banana=bioregistry.get_banana(prefix),
        description=bioregistry.get_description(prefix),
        providers=None if example is None else _get_resource_providers(prefix, example),
        formats=[
            *FORMATS,
            ("RDF (turtle)", "turtle"),
            ("RDF (JSON-LD)", "jsonld"),
        ],
    )


@ui_blueprint.route("/metaregistry/<metaprefix>")
def metaresource(metaprefix: str):
    """Serve the a Bioregistry registry page."""
    entry = bioregistry.get_registry(metaprefix)
    if entry is None:
        return abort(404, f"Invalid metaprefix: {metaprefix}")

    example_identifier = bioregistry.get_example(entry.example)
    return render_template(
        "metaresource.html",
        entry=entry,
        metaprefix=metaprefix,
        name=bioregistry.get_registry_name(metaprefix),
        description=bioregistry.get_registry_description(metaprefix),
        homepage=bioregistry.get_registry_homepage(metaprefix),
        download=entry.download,
        example_prefix=entry.example,
        example_prefix_url=entry.get_provider_uri_format(entry.example),
        example_identifier=example_identifier,
        example_curie=(
            curie_to_str(entry.example, example_identifier) if example_identifier else None
        ),
        example_curie_url=(
            bioregistry.get_registry_uri(metaprefix, entry.example, example_identifier)
            if example_identifier
            else None
        ),
        formats=[
            *FORMATS,
            ("RDF (turtle)", "turtle"),
            ("RDF (JSON-LD)", "jsonld"),
        ],
    )


@ui_blueprint.route("/collection/<identifier>")
def collection(identifier: str):
    """Serve the a Bioregistry registry page."""
    entry = bioregistry.get_collection(identifier)
    if entry is None:
        abort(404, f"Invalid collection: {identifier}")
    return render_template(
        "collection.html",
        identifier=identifier,
        entry=entry,
        formats=[
            *FORMATS,
            ("RDF (turtle)", "turtle"),
            ("RDF (JSON-LD)", "jsonld"),
            ("Context JSON-LD", "context"),
        ],
    )


@ui_blueprint.route("/reference/<prefix>:<path:identifier>")
def reference(prefix: str, identifier: str):
    """Serve the a Bioregistry reference page."""
    return render_template(
        "reference.html",
        prefix=prefix,
        name=bioregistry.get_name(prefix),
        identifier=identifier,
        providers=_get_resource_providers(prefix, identifier),
        formats=FORMATS,
    )


@ui_blueprint.route("/<prefix>")
@ui_blueprint.route("/<prefix>:<path:identifier>")
def resolve(prefix: str, identifier: Optional[str] = None):
    """Resolve a CURIE.

    The following things can make a CURIE unable to resolve:

    1. The prefix is not registered with the Bioregistry
    2. The prefix has a validation pattern and the identifier does not match it
    3. There are no providers available for the URL
    """  # noqa:DAR101,DAR201
    norm_prefix = bioregistry.normalize_prefix(prefix)
    if norm_prefix is None:
        return (
            render_template(
                "resolve_errors/missing_prefix.html", prefix=prefix, identifier=identifier
            ),
            404,
        )
    if identifier is None:
        return redirect(url_for("." + resource.__name__, prefix=norm_prefix))

    pattern = bioregistry.get_pattern(prefix)
    if pattern and not bioregistry.is_known_identifier(prefix, identifier):
        return (
            render_template(
                "resolve_errors/invalid_identifier.html",
                prefix=prefix,
                identifier=identifier,
                pattern=pattern,
            ),
            404,
        )

    url = bioregistry.get_iri(prefix, identifier, use_bioregistry_io=False)
    if not url:
        return (
            render_template(
                "resolve_errors/missing_providers.html", prefix=prefix, identifier=identifier
            ),
            404,
        )
    try:
        # TODO remove any garbage characters?
        return redirect(url)
    except ValueError:  # headers could not be constructed
        return (
            render_template(
                "resolve_errors/disallowed_identifier.html", prefix=prefix, identifier=identifier
            ),
            404,
        )


@ui_blueprint.route("/contributors/")
def contributors():
    """Serve the Bioregistry contributors page."""
    return render_template(
        "contributors.html",
        rows=bioregistry.read_contributors().values(),
        collections=read_collections_contributions(),
        prefix_contributions=read_prefix_contributions(),
        prefix_reviews=read_prefix_reviews(),
        formats=FORMATS,
    )


@ui_blueprint.route("/contributor/<orcid>")
def contributor(orcid: str):
    """Serve the a Bioregistry contributor page."""
    author = bioregistry.read_contributors().get(orcid)
    if author is None:
        return abort(404)
    return render_template(
        "contributor.html",
        contributor=author,
        collections=sorted(
            (collection_id, bioregistry.get_collection(collection_id))
            for collection_id in read_collections_contributions().get(author.orcid, [])
        ),
        prefix_contributions=_s(read_prefix_contributions().get(author.orcid, [])),
        prefix_reviews=_s(read_prefix_reviews().get(author.orcid, [])),
        formats=FORMATS,
    )


def _s(prefixes):
    return sorted((p, bioregistry.get_resource(p)) for p in prefixes)
