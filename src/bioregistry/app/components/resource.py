"""A route for a resource."""

from __future__ import annotations

import json

import werkzeug
from flask import render_template

from .base import ui_blueprint
from ..constants import FORMATS
from ..proxies import manager
from ..utils import (
    _get_resource_providers,
    _normalize_prefix_or_404,
    get_accept_media_type,
    serialize_model,
)
from ...export.rdf_export import resource_to_rdf_str

__all__ = ["resource"]


@ui_blueprint.route("/registry/<prefix>")
def resource(prefix: str) -> str | werkzeug.Response | tuple[str, int]:
    """Serve a resource page."""
    norm_prefix = _normalize_prefix_or_404(prefix, "." + resource.__name__)
    if not isinstance(norm_prefix, str):
        return norm_prefix
    _resource = manager.get_resource(norm_prefix)
    if _resource is None:
        raise RuntimeError
    accept = get_accept_media_type()
    if accept != "text/html":
        return serialize_model(_resource, resource_to_rdf_str, negotiate=True)

    example = _resource.get_example()
    example_curie = _resource.get_example_curie(use_preferred=True)
    example_extras = _resource.get_example_extras()
    example_curie_extras = [
        _resource.get_curie(example_extra, use_preferred=True) for example_extra in example_extras
    ]
    name_pack = manager._repack(_resource.get_name(provenance=True))
    return render_template(
        "resource.html",
        zip=zip,
        prefix=prefix,
        resource=_resource,
        bioschemas=json.dumps(_resource.get_bioschemas_jsonld(), ensure_ascii=False),
        name_pack=name_pack,
        example=example,
        example_extras=example_extras,
        example_curie=example_curie,
        example_curie_extras=example_curie_extras,
        mappings=[
            {
                "metaprefix": metaprefix,
                "metaresource": manager.get_registry(metaprefix),
                "xref": xref,
                "homepage": manager.get_registry_homepage(metaprefix),
                "name": manager.get_registry_name(metaprefix),
                "short_name": manager.get_registry_short_name(metaprefix),
                "uri": manager.get_registry_provider_uri_format(metaprefix, xref),
            }
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
        skos_download=_resource.get_download_skos(),
        jskos_download=_resource.get_download_jskos(),
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
