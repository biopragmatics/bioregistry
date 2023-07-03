# -*- coding: utf-8 -*-

"""User blueprint for the bioregistry web application."""

import datetime
import itertools as itt
import json
import platform
from collections import defaultdict
from operator import attrgetter
from pathlib import Path
from typing import Optional

from flask import (
    Blueprint,
    abort,
    current_app,
    jsonify,
    redirect,
    render_template,
    request,
    url_for,
)

from .proxies import manager
from .utils import (
    _get_resource_providers,
    _normalize_prefix_or_404,
    get_accept_media_type,
    serialize_model,
)
from .. import version
from ..constants import NDEX_UUID
from ..export.rdf_export import (
    collection_to_rdf_str,
    metaresource_to_rdf_str,
    resource_to_rdf_str,
)
from ..schema import Context
from ..schema.constants import bioregistry_schema_terms
from ..schema.struct import (
    Registry,
    RegistryGovernance,
    RegistryQualities,
    RegistrySchema,
    get_json_schema,
    schema_status_map,
)
from ..schema_utils import (
    read_collections_contributions,
    read_context_contributions,
    read_prefix_contacts,
    read_prefix_contributions,
    read_prefix_reviews,
    read_registry_contributions,
)
from ..utils import curie_to_str

__all__ = [
    "ui_blueprint",
]

TEMPLATES = Path(__file__).parent.resolve().joinpath("templates")
ui_blueprint = Blueprint("metaregistry_ui", __name__, template_folder=TEMPLATES)

FORMATS = [
    ("JSON", "json"),
    ("YAML", "yaml"),
]


@ui_blueprint.route("/registry/")
def resources():
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
def metaresources():
    """Serve the metaregistry page."""
    return render_template(
        "metaresources.html",
        rows=manager.metaregistry.values(),
        formats=FORMATS,
    )


@ui_blueprint.route("/collection/")
def collections():
    """Serve the collections page."""
    return render_template(
        "collections.html",
        rows=manager.collections.items(),
        formats=FORMATS,
    )


@ui_blueprint.route("/registry/<prefix>")
def resource(prefix: str):
    """Serve a resource page."""
    prefix = _normalize_prefix_or_404(prefix, "." + resource.__name__)
    if not isinstance(prefix, str):
        return prefix
    _resource = manager.get_resource(prefix)
    if _resource is None:
        raise RuntimeError
    accept = get_accept_media_type()
    if accept != "text/html":
        return serialize_model(_resource, resource_to_rdf_str, negotiate=True)

    example = _resource.get_example()
    example_curie = _resource.get_example_curie(use_preferred=True)
    example_extras = _resource.example_extras or []
    example_curie_extras = [
        _resource.get_curie(example_extra, use_preferred=True) for example_extra in example_extras
    ]
    return render_template(
        "resource.html",
        zip=zip,
        prefix=prefix,
        resource=_resource,
        bioschemas=json.dumps(_resource.get_bioschemas_jsonld(), ensure_ascii=False),
        name=manager.get_name(prefix),
        example=example,
        example_extras=example_extras,
        example_curie=example_curie,
        example_curie_extras=example_curie_extras,
        mappings=[
            dict(
                metaprefix=metaprefix,
                metaresource=manager.get_registry(metaprefix),
                xref=xref,
                homepage=manager.get_registry_homepage(metaprefix),
                name=manager.get_registry_name(metaprefix),
                short_name=manager.get_registry_short_name(metaprefix),
                uri=manager.get_registry_provider_uri_format(metaprefix, xref),
            )
            for metaprefix, xref in _resource.get_mappings().items()
        ],
        synonyms=_resource.get_synonyms(),
        homepage=_resource.get_homepage(),
        repository=_resource.get_repository(),
        pattern=manager.get_pattern(prefix),
        curie_pattern=manager.get_curie_pattern(prefix, use_preferred=True),
        version=_resource.get_version(),
        has_no_terms=manager.has_no_terms(prefix),
        obo_download=_resource.get_download_obo(),
        owl_download=_resource.get_download_owl(),
        json_download=_resource.get_download_obograph(),
        rdf_download=_resource.get_download_rdf(),
        namespace_in_lui=_resource.get_namespace_in_lui(),
        deprecated=manager.is_deprecated(prefix),
        contact=_resource.get_contact(),
        banana=_resource.get_banana(),
        description=manager.get_description(prefix, use_markdown=True),
        appears_in=manager.get_appears_in(prefix),
        depends_on=manager.get_depends_on(prefix),
        has_canonical=manager.get_has_canonical(prefix),
        canonical_for=manager.get_canonical_for(prefix),
        provides=manager.get_provides_for(prefix),
        provided_by=manager.get_provided_by(prefix),
        part_of=manager.get_part_of(prefix),
        has_parts=manager.get_has_parts(prefix),
        in_collections=manager.get_in_collections(prefix),
        providers=None if example is None else _get_resource_providers(prefix, example),
        formats=[
            *FORMATS,
            ("RDF (turtle)", "turtle"),
            ("RDF (JSON-LD)", "jsonld"),
            ("RDF (n3)", "n3"),
        ],
    )


@ui_blueprint.route("/metaregistry/<metaprefix>")
def metaresource(metaprefix: str):
    """Serve a metaresource page."""
    entry = manager.metaregistry.get(metaprefix)
    if entry is None:
        return abort(404, f"Invalid metaprefix: {metaprefix}")
    accept = get_accept_media_type()
    if accept != "text/html":
        return serialize_model(entry, metaresource_to_rdf_str, negotiate=True)

    example_identifier = manager.get_example(entry.example)
    return render_template(
        "metaresource.html",
        entry=entry,
        metaprefix=metaprefix,
        name=entry.name,
        description=entry.description,
        homepage=entry.homepage,
        download=entry.download,
        example_prefix=entry.example,
        example_prefix_url=entry.get_provider_uri_format(entry.example),
        example_identifier=example_identifier,
        example_curie=(
            curie_to_str(entry.example, example_identifier) if example_identifier else None
        ),
        example_curie_url=(
            manager.get_registry_uri(metaprefix, entry.example, example_identifier)
            if example_identifier
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
def obo_health(prefix: str):
    """Serve a redirect to OBO Foundry community health image."""
    url = manager.get_obo_health_url(prefix)
    if url is None:
        abort(404, f"Missing OBO prefix {prefix}")
    return redirect(url)


@ui_blueprint.route("/collection/<identifier>")
def collection(identifier: str):
    """Serve a collection page."""
    entry = manager.collections.get(identifier)
    if entry is None:
        return abort(404, f"Invalid collection: {identifier}")
    accept = get_accept_media_type()
    if accept != "text/html":
        return serialize_model(entry, collection_to_rdf_str, negotiate=True)

    return render_template(
        "collection.html",
        identifier=identifier,
        entry=entry,
        resources={prefix: manager.get_resource(prefix) for prefix in entry.resources},
        formats=[
            *FORMATS,
            ("Context (JSON-LD)", "context"),
            ("RDF (turtle)", "turtle"),
            ("RDF (JSON-LD)", "jsonld"),
            ("RDF (n3)", "n3"),
        ],
    )


@ui_blueprint.route("/context/")
def contexts():
    """Serve the contexts page."""
    return render_template(
        "contexts.html",
        rows=manager.contexts.items(),
        formats=FORMATS,
        schema=Context.schema(),
    )


@ui_blueprint.route("/context/<identifier>")
def context(identifier: str):
    """Serve a context page."""
    entry = manager.contexts.get(identifier)
    if entry is None:
        return abort(404, f"Invalid context: {identifier}")
    return render_template(
        "context.html",
        identifier=identifier,
        entry=entry,
        schema=Context.schema()["properties"],
        formats=FORMATS,
    )


@ui_blueprint.route("/reference/<prefix>:<path:identifier>")
def reference(prefix: str, identifier: str):
    """Serve a reference page."""
    return render_template(
        "reference.html",
        prefix=prefix,
        name=manager.get_name(prefix),
        identifier=identifier,
        providers=_get_resource_providers(prefix, identifier),
        formats=FORMATS,
    )


@ui_blueprint.route("/<prefix>")
@ui_blueprint.route("/<prefix>:<path:identifier>")
def resolve(prefix: str, identifier: Optional[str] = None):
    """Resolve a CURIE.

    The following things can make a CURIE unable to resolve:

    1. The prefix is not registered
    2. The prefix has a validation pattern and the identifier does not match it
    3. There are no providers available for the URL
    """  # noqa:DAR101,DAR201
    _resource = manager.get_resource(prefix)
    if _resource is None:
        return (
            render_template(
                "resolve_errors/missing_prefix.html", prefix=prefix, identifier=identifier
            ),
            404,
        )
    if identifier is None:
        return redirect(url_for("." + resource.__name__, prefix=_resource.prefix))

    identifier = _resource.standardize_identifier(identifier)

    pattern = _resource.get_pattern()
    if pattern and not _resource.is_valid_identifier(identifier):
        return (
            render_template(
                "resolve_errors/invalid_identifier.html",
                prefix=prefix,
                identifier=identifier,
                pattern=pattern,
            ),
            404,
        )

    url = manager.get_iri(
        prefix,
        identifier,
        use_bioregistry_io=False,
        provider=request.args.get("provider"),
    )
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


@ui_blueprint.route("/metaregistry/<metaprefix>/<metaidentifier>")
@ui_blueprint.route("/metaregistry/<metaprefix>/<metaidentifier>:<path:identifier>")
def metaresolve(metaprefix: str, metaidentifier: str, identifier: Optional[str] = None):
    """Redirect to a prefix page or meta-resolve the CURIE.

    Test this function locally with:

    - http://localhost:5000/metaregistry/obofoundry/GO
    - http://localhost:5000/metaregistry/obofoundry/GO:0032571
    """  # noqa:DAR101,DAR201
    if metaprefix not in manager.metaregistry:
        return abort(404, f"invalid metaprefix: {metaprefix}")
    prefix = manager.lookup_from(metaprefix, metaidentifier, normalize=True)
    if prefix is None:
        return abort(
            404,
            f"Could not map {metaidentifier} in {metaprefix} to a Bioregistry prefix."
            f" The Bioregistry contains mappings for the following:"
            f" {list(manager.get_registry_invmap(metaprefix))}",
        )
    return redirect(url_for(f".{resolve.__name__}", prefix=prefix, identifier=identifier))


@ui_blueprint.route("/resolve/github/issue/<owner>/<repository>/<int:issue>")
def github_resolve_issue(owner, repository, issue):
    """Redirect to an issue on GitHub."""
    return redirect(f"https://github.com/{owner}/{repository}/issues/{issue}")


@ui_blueprint.route("/resolve/github/pull/<owner>/<repository>/<int:pull>")
def github_resolve_pull(owner, repository, pull: int):
    """Redirect to a pull request on GitHub."""
    return redirect(f"https://github.com/{owner}/{repository}/pull/{pull}")


@ui_blueprint.route("/contributors/")
def contributors():
    """Serve the contributors page."""
    collections = read_collections_contributions(manager.collections)
    contexts = read_context_contributions(manager.contexts)
    prefix_contributions = read_prefix_contributions(manager.registry)
    prefix_reviews = read_prefix_reviews(manager.registry)
    prefix_contacts = read_prefix_contacts(manager.registry)
    registries = read_registry_contributions(manager.metaregistry)
    unique_direct_count = len(
        set(itt.chain(collections, contexts, prefix_contributions, prefix_reviews))
    )
    unique_indirect_count = len(set(itt.chain(prefix_contacts, registries)))
    return render_template(
        "contributors.html",
        rows=manager.read_contributors().values(),
        collections=collections,
        contexts=contexts,
        prefix_contributions=prefix_contributions,
        prefix_reviews=prefix_reviews,
        prefix_contacts=prefix_contacts,
        registries=registries,
        formats=FORMATS,
        unique_direct_count=unique_direct_count,
        unique_indirect_count=unique_indirect_count,
    )


@ui_blueprint.route("/contributor/<orcid>")
def contributor(orcid: str):
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


def _s(prefixes):
    return sorted((p, manager.get_resource(p)) for p in prefixes)


@ui_blueprint.route("/")
def home():
    """Render the homepage."""
    example_prefix = current_app.config["METAREGISTRY_EXAMPLE_PREFIX"]
    example_identifier = manager.get_example(example_prefix)
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


@ui_blueprint.route("/summary")
def summary():
    """Render the summary page."""
    return render_template("meta/summary.html")


@ui_blueprint.route("/related")
def related():
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


@ui_blueprint.route("/download")
def download():
    """Render the download page."""
    return render_template("meta/download.html", ndex_uuid=NDEX_UUID)


@ui_blueprint.route("/acknowledgements")
def acknowledgements():
    """Render the acknowledgements page."""
    return render_template(
        "meta/acknowledgements.html",
        registries=sorted(manager.metaregistry.values(), key=attrgetter("name")),
    )


_VERSION = version.get_version()
_GIT_HASH = version.get_git_hash()
_PLATFORM = platform.platform()
_PLATFORM_VERSION = platform.version()
_PYTHON_VERSION = platform.python_version()
_DEPLOYED = datetime.datetime.now()


@ui_blueprint.route("/sustainability")
def sustainability():
    """Render the sustainability page."""
    return render_template(
        "meta/sustainability.html",
        software_version=_VERSION,
        software_git_hash=_GIT_HASH,
        platform=_PLATFORM,
        platform_version=_PLATFORM_VERSION,
        python_version=_PYTHON_VERSION,
        deployed=_DEPLOYED,
    )


@ui_blueprint.route("/usage")
def usage():
    """Render the programmatic usage page."""
    resource = manager.get_resource(current_app.config["METAREGISTRY_EXAMPLE_PREFIX"])
    return render_template("meta/access.html", resource=resource)


@ui_blueprint.route("/schema/")
def schema():
    """Render the Bioregistry RDF schema."""
    return render_template("meta/schema.html", terms=bioregistry_schema_terms)


@ui_blueprint.route("/schema.json")
def json_schema():
    """Return the JSON schema."""
    return jsonify(get_json_schema())


@ui_blueprint.route("/highlights/twitter")
def highlights_twitter():
    """Render the twitter highlights page."""
    twitters = defaultdict(list)
    for resource in manager.registry.values():
        twitter = resource.get_twitter()
        if twitter:
            twitters[twitter].append(resource)
    return render_template("highlights/twitter.html", twitters=twitters)


@ui_blueprint.route("/highlights/relations")
def highlights_relations():
    """Render the relations highlights page."""
    return render_template("highlights/relations.html")


@ui_blueprint.route("/highlights/keywords")
def highlights_keywords():
    """Render the keywords highlights page."""
    keyword_to_prefix = defaultdict(list)
    for resource in manager.registry.values():
        for keyword in resource.get_keywords():
            keyword_to_prefix[keyword].append(resource)

    return render_template("highlights/keywords.html", keywords=keyword_to_prefix)


@ui_blueprint.route("/highlights/owners")
def highlights_owners():
    """Render the partners highlights page."""
    owner_to_resources = defaultdict(list)
    owners = {}
    for resource in manager.registry.values():
        for owner in resource.owners or []:
            owners[owner.pair] = owner
            owner_to_resources[owner.pair].append(resource)
    return render_template(
        "highlights/owners.html", owners=owners, owner_to_resources=owner_to_resources
    )


@ui_blueprint.route("/apidocs")
@ui_blueprint.route("/apidocs/")
def apidocs():
    """Render api documentation page."""
    return redirect("/docs")
