"""User blueprint for the web application."""

from __future__ import annotations

import itertools as itt
import json
from collections import defaultdict
from collections.abc import Iterable
from operator import attrgetter
from typing import cast

import flask
import werkzeug
from curies import Reference
from flask import abort, current_app, jsonify, redirect, render_template, request, url_for

from .components.base import ui_blueprint
from .components.resolver import _clean_reference, resolve
from .constants import FORMATS
from .proxies import manager
from .utils import (
    ResponseWrapperError,
    _get_resource_providers,
    get_accept_media_type,
    serialize_model,
)
from ..constants import INTERNAL_LABEL, INTERNAL_METAPREFIX, NFDI_ROR
from ..export.rdf_export import collection_to_rdf_str, metaresource_to_rdf_str
from ..schema import (
    Context,
    Registry,
    RegistryGovernance,
    RegistryQualities,
    RegistrySchema,
    Resource,
    get_json_schema,
    schema_status_map,
)
from ..schema.struct import Collection, Organization, filter_collections
from ..schema_utils import (
    read_collections_contributions,
    read_context_contributions,
    read_prefix_contacts,
    read_prefix_contributions,
    read_prefix_reviews,
    read_registry_contributions,
    read_status_contributions,
)
from ..utils import curie_to_str

__all__ = ["ui_blueprint"]


@ui_blueprint.route("/registry/")
def resources() -> str:
    """Serve the registry page."""
    registry = manager.registry
    if request.args.get("novel") in {"true", "t"}:
        registry = {p: v for p, v in registry.items() if manager.is_novel(p)}
    return render_template(
        "resources.html",
        formats=FORMATS,
        registry=registry,
    )


@ui_blueprint.route("/metaregistry/")
def metaresources() -> str:
    """Serve the metaregistry page."""
    return render_template(
        "metaresources.html",
        rows=manager.metaregistry.values(),
        formats=FORMATS,
    )


@ui_blueprint.route("/collection/")
def collections() -> str:
    """Serve the collections page."""
    collections_: list[Collection] = list(manager.collections.values())
    organization: Organization | None = None
    if ror := flask.request.args.get("ror"):
        collections_ = filter_collections(collections_, ror)
        if not collections_:
            raise flask.abort(404, f"no collections are tagged with ROR: {ror}")
        organization = next(org for org in collections_[0].organizations or [] if org.ror == ror)
    return render_template(
        "collections.html",
        collections=collections_,
        formats=FORMATS,
        ror=ror,
        organization=organization,
    )


@ui_blueprint.route("/metaregistry/<metaprefix>")
def metaresource(metaprefix: str) -> str | flask.Response:
    """Serve a metaresource page."""
    entry = manager.metaregistry.get(metaprefix)
    if entry is None:
        return abort(404, f"Invalid metaprefix: {metaprefix}")
    accept = get_accept_media_type()
    if accept != "text/html":
        return serialize_model(entry, metaresource_to_rdf_str, negotiate=True)

    external_prefix = entry.example
    internal_prefix: str | None
    if metaprefix == INTERNAL_METAPREFIX:
        internal_prefix = external_prefix
    else:
        # TODO change this to [external_prefix] instead of .get(external_prefix)
        #  when all metaregistry entries are required to have corresponding schema slots
        internal_prefix = manager.get_registry_invmap(metaprefix).get(external_prefix)

    # In the case that we can't map from the external registry's prefix to the internal
    # prefix, the example identifier can't be looked up
    example_identifier = internal_prefix and manager.get_example(internal_prefix)
    return render_template(
        "metaresource.html",
        entry=entry,
        metaprefix=metaprefix,
        name=entry.name,
        description=entry.description,
        homepage=entry.homepage,
        download=entry.download,
        example_prefix=external_prefix,
        example_prefix_url=entry.get_provider_uri_format(external_prefix),
        example_identifier=example_identifier,
        example_curie=(
            curie_to_str(external_prefix, example_identifier) if example_identifier else None
        ),
        example_curie_url=(
            # TODO there must be a more direct way for this
            manager.get_registry_uri(metaprefix, internal_prefix, example_identifier)
            if internal_prefix and example_identifier
            else None
        ),
        formats=[
            *FORMATS,
            ("RDF (turtle)", "turtle"),
            ("RDF (JSON-LD)", "jsonld"),
            ("RDF (n3)", "n3"),
        ],
    )


@ui_blueprint.route("/health/<prefix>")
def obo_health(prefix: str) -> werkzeug.Response:
    """Serve a redirect to OBO Foundry community health image."""
    url = manager.get_obo_health_url(prefix)
    if url is None:
        abort(404, f"Missing OBO prefix {prefix}")
    return redirect(url)


@ui_blueprint.route("/collection/<identifier>")
def collection(identifier: str) -> str | flask.Response:
    """Serve a collection page."""
    entry = manager.collections.get(identifier)
    if entry is None:
        return abort(404, f"Invalid collection: {identifier}")
    accept = get_accept_media_type()
    if accept != "text/html":
        return serialize_model(entry, collection_to_rdf_str, negotiate=True)
    indirect = manager.get_collection_indirect_dependencies(entry)
    first_party = manager.get_collection_first_party(entry, skip_org_rors={NFDI_ROR})
    tags = {tag.code: tag for tag in entry.tags or []}
    return render_template(
        "collection.html",
        identifier=identifier,
        entry=entry,
        resources={
            prefix: manager.get_resource(prefix, strict=True) for prefix in entry.get_prefixes()
        },
        indirect=indirect,
        first_party=first_party,
        tags=tags,
        formats=[
            *FORMATS,
            ("Context (JSON-LD)", "context"),
            ("RDF (turtle)", "turtle"),
            ("RDF (JSON-LD)", "jsonld"),
            ("RDF (n3)", "n3"),
        ],
    )


@ui_blueprint.route("/context/")
def contexts() -> str:
    """Serve the contexts page."""
    return render_template(
        "contexts.html",
        rows=manager.contexts.items(),
        formats=FORMATS,
        schema=Context.model_json_schema(),
    )


@ui_blueprint.route("/context/<identifier>")
def context(identifier: str) -> str:
    """Serve a context page."""
    entry = manager.contexts.get(identifier)
    if entry is None:
        return abort(404, f"Invalid context: {identifier}")
    return render_template(
        "context.html",
        identifier=identifier,
        entry=entry,
        schema=Context.model_json_schema()["properties"],
        formats=FORMATS,
    )


@ui_blueprint.route("/reference/<prefix>:<path:identifier>")
@ui_blueprint.route("/reference/<prefix>:/<path:identifier>")  # ARK hack, see below
def reference(
    prefix: str, identifier: str
) -> str | werkzeug.Response | tuple[str | werkzeug.Response, int]:
    """Serve a reference page."""
    try:
        _resource, reference_ = _clean_reference(prefix, identifier)
    except ResponseWrapperError as rw:
        return rw.get_value()
    identifier = reference_.identifier
    return render_template(
        "reference.html",
        prefix=_resource.prefix,
        name=_resource.get_name(),
        identifier=identifier,
        providers=_get_resource_providers(_resource.prefix, identifier),
        formats=[
            *FORMATS,
            ("RDF (turtle)", "turtle"),
        ],
    )


@ui_blueprint.route("/metaregistry/<metaprefix>/<metaidentifier>")
@ui_blueprint.route("/metaregistry/<metaprefix>/<metaidentifier>:<path:identifier>")
def metaresolve(
    metaprefix: str, metaidentifier: str, identifier: str | None = None
) -> werkzeug.Response:
    """Redirect to a prefix page or meta-resolve the CURIE.

    Test this function locally with:

    - http://localhost:5000/metaregistry/obofoundry/GO
    - http://localhost:5000/metaregistry/obofoundry/GO:0032571
    """
    if metaprefix not in manager.metaregistry:
        return abort(404, f"invalid metaprefix: {metaprefix}")
    prefix = manager.lookup_from(metaprefix, metaidentifier)
    if prefix is None:
        return abort(
            404,
            f"Could not map {metaidentifier} in {metaprefix} to a {INTERNAL_LABEL} prefix."
            f" The {INTERNAL_LABEL} contains mappings for the following:"
            f" {list(manager.get_registry_invmap(metaprefix))}",
        )
    return redirect(url_for(f".{resolve.__name__}", prefix=prefix, identifier=identifier))


@ui_blueprint.route("/contributors/")
def contributors() -> str:
    """Serve the contributors page."""
    collections = read_collections_contributions(manager.collections)
    contexts = read_context_contributions(manager.contexts)
    prefix_contributions = read_prefix_contributions(manager.registry)
    prefix_reviews = read_prefix_reviews(manager.registry)
    prefix_contacts = read_prefix_contacts(manager.registry)
    registries = read_registry_contributions(manager.metaregistry)
    status_contributions = read_status_contributions(manager.registry)
    unique_direct_count = len(
        set(itt.chain(collections, contexts, prefix_contributions, prefix_reviews))
    )
    unique_indirect_count = len(set(itt.chain(prefix_contacts, registries)))
    return render_template(
        "contributors.html",
        rows=manager.read_contributors(direct_only=True).values(),
        collections=collections,
        contexts=contexts,
        prefix_contributions=prefix_contributions,
        prefix_reviews=prefix_reviews,
        prefix_contacts=prefix_contacts,
        registries=registries,
        formats=FORMATS,
        unique_direct_count=unique_direct_count,
        unique_indirect_count=unique_indirect_count,
        status_contributions=status_contributions,
    )


@ui_blueprint.route("/contributor/<orcid>")
def contributor(orcid: str) -> werkzeug.Response | str:
    """Serve a contributor page."""
    author = manager.read_contributors().get(orcid)
    if author is None or author.orcid is None:
        return abort(404)
    return render_template(
        "contributor.html",
        contributor=author,
        collections=sorted(
            (collection_id, manager.collections.get(collection_id))
            for collection_id in read_collections_contributions(manager.collections).get(
                author.orcid, []
            )
        ),
        contexts=sorted(
            (context_key, manager.contexts.get(context_key))
            for context_key in read_context_contributions(manager.contexts).get(author.orcid, [])
        ),
        prefix_contributions=_s(read_prefix_contributions(manager.registry).get(author.orcid, [])),
        prefix_contacts=_s(read_prefix_contacts(manager.registry).get(author.orcid, [])),
        prefix_reviews=_s(read_prefix_reviews(manager.registry).get(author.orcid, [])),
        registries=_s(read_registry_contributions(manager.metaregistry).get(author.orcid, [])),
        formats=FORMATS,
    )


def _s(prefixes: Iterable[str]) -> list[tuple[str, Resource | None]]:
    return sorted((p, manager.get_resource(p)) for p in prefixes)


@ui_blueprint.route("/")
def home() -> str:
    """Render the homepage."""
    example_prefix = current_app.config["METAREGISTRY_EXAMPLE_PREFIX"]
    example_identifier = manager.get_example(example_prefix)
    if example_identifier is None:
        raise RuntimeError("app should be configured with valid example")
    example_url = manager.get_bioregistry_iri(example_prefix, example_identifier)
    bioschemas = current_app.config.get("METAREGISTRY_BIOSCHEMAS")
    return render_template(
        "home.html",
        example_url=example_url,
        example_prefix=example_prefix,
        example_identifier=example_identifier,
        registry_size=len(manager.registry),
        metaregistry_size=len(manager.metaregistry),
        collections_size=len(manager.collections),
        contributors_size=len(manager.read_contributors()),
        bioschemas=json.dumps(bioschemas, ensure_ascii=False) if bioschemas else None,
    )


@ui_blueprint.route("/related")
def related() -> str:
    """Render the related page."""
    return render_template(
        "meta/related.html",
        mapping_counts=manager.count_mappings(),
        registries=sorted(manager.metaregistry.values(), key=attrgetter("name")),
        schema_status_map=schema_status_map,
        registry_cls=Registry,
        registry_governance_cls=RegistryGovernance,
        registry_schema_cls=RegistrySchema,
        registry_qualities_cls=RegistryQualities,
    )


@ui_blueprint.route("/schema.json")
def json_schema() -> werkzeug.Response:
    """Return the JSON schema."""
    return jsonify(get_json_schema())  # type:ignore


@ui_blueprint.route("/keywords")
def highlights_keywords() -> werkzeug.Response:
    """Redirect to the keywords index."""
    return redirect(url_for("." + get_keywords.__name__))


@ui_blueprint.route("/keyword")
def get_keywords() -> str:
    """Render the keywords highlights page."""
    keyword_to_prefix = manager.get_keyword_to_resources()
    return render_template("keywords.html", keywords=keyword_to_prefix)


@ui_blueprint.route("/keyword/<keyword>")
def get_keyword(keyword: str) -> str:
    """Render the keywords highlights page."""
    resources_ = manager.get_resources_with_keyword(keyword)
    return render_template("keyword.html", keyword=keyword, resources=resources_)


@ui_blueprint.route("/organization/")
def show_organizations() -> str:
    """Render the partners highlights page."""
    owner_to_resources = defaultdict(list)
    owners = {}
    for resource_ in manager.registry.values():
        for owner in resource_.get_owners():
            curie = owner.reference.curie
            owners[curie] = owner
            owner_to_resources[curie].append(resource_)
    return render_template(
        "organizations.html", owners=owners, owner_to_resources=owner_to_resources
    )


@ui_blueprint.route("/organization/<curie>")
def show_organization(curie: str) -> str:
    """Show an organization."""
    reference_ = Reference.from_curie(curie)
    resources_ = [
        resource_
        for resource_ in manager.registry.values()
        if resource_.has_organization(reference_)
    ]
    collections_ = [c for c in manager.collections.values() if c.has_organization(reference_)]
    if not resources_ and not collections_:
        raise flask.abort(404)
    elif resources_:
        organization = next(
            o for o in resources_[0].get_owners() if o.matches_reference(reference_)
        )
    else:
        organization = next(
            o
            for o in cast(list[Organization], collections_[0].organizations)
            if o.matches_reference(reference_)
        )
    return render_template(
        "organization.html",
        organization=organization,
        resources=resources_,
        collections=collections_,
    )


@ui_blueprint.route("/apidocs")
@ui_blueprint.route("/apidocs/")
def apidocs() -> werkzeug.Response:
    """Render api documentation page."""
    return redirect("/docs")
