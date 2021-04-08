# -*- coding: utf-8 -*-

"""User blueprint for the bioregistry web application."""

from flask import Blueprint, abort, redirect, render_template

import bioregistry
from .utils import _get_resource_mapping_rows, _get_resource_providers, _normalize_prefix_or_404

__all__ = [
    'ui_blueprint',
]

ui_blueprint = Blueprint('ui', __name__)


@ui_blueprint.route('/registry/')
def resources():
    """Serve the Bioregistry page."""
    rows = [
        dict(
            prefix=prefix,
            name=bioregistry.get_name(prefix),
            example=bioregistry.get_example(prefix),
            homepage=bioregistry.get_homepage(prefix),
            pattern=bioregistry.get_pattern(prefix),
            namespace_in_lui=bioregistry.namespace_in_lui(prefix),
            banana=bioregistry.get_banana(prefix),
            description=bioregistry.get_description(prefix),
        )
        for prefix in bioregistry.read_bioregistry()
    ]
    return render_template('resources.html', rows=rows)


@ui_blueprint.route('/registry/<prefix>')
def resource(prefix: str):
    """Serve the a Bioregistry entry page."""
    prefix = _normalize_prefix_or_404(prefix, ui_blueprint.name + '.' + resource.__name__)
    if not isinstance(prefix, str):
        return prefix
    example = bioregistry.get_example(prefix)
    return render_template(
        'resource.html',
        prefix=prefix,
        name=bioregistry.get_name(prefix),
        example=example,
        mappings=_get_resource_mapping_rows(prefix),
        synonyms=bioregistry.get_synonyms(prefix),
        homepage=bioregistry.get_homepage(prefix),
        pattern=bioregistry.get_pattern(prefix),
        version=bioregistry.get_version(prefix),
        namespace_in_lui=bioregistry.namespace_in_lui(prefix),
        deprecated=bioregistry.is_deprecated(prefix),
        contact=bioregistry.get_email(prefix),
        banana=bioregistry.get_banana(prefix),
        description=bioregistry.get_description(prefix),
        providers=None if example is None else _get_resource_providers(prefix, example),
    )


@ui_blueprint.route('/reference/<prefix>:<identifier>')
def reference(prefix: str, identifier: str):
    """Serve the a Bioregistry reference page."""
    return render_template(
        'reference.html',
        prefix=prefix,
        name=bioregistry.get_name(prefix),
        identifier=identifier,
        providers=_get_resource_providers(prefix, identifier),
    )


@ui_blueprint.route('/<prefix>:<identifier>')
def resolve(prefix: str, identifier: str):
    """Resolve a CURIE."""
    url = bioregistry.get_link(prefix, identifier)
    if not url:
        abort(400)
    return redirect(url)
