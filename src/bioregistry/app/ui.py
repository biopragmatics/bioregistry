# -*- coding: utf-8 -*-

"""User blueprint for the bioregistry web application."""

from flask import Blueprint, redirect, render_template, url_for

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


@ui_blueprint.route('/metaregistry/')
def metaresources():
    """Serve the Bioregistry metaregistry page."""
    return render_template('metaresources.html', rows=bioregistry.read_metaregistry().values())


@ui_blueprint.route('/<prefix>')
def resource_redirect(prefix: str):
    """Redirect to the canonical endpoint for serving prefix information."""
    return redirect(url_for('.' + resource.__name__, prefix=prefix))


@ui_blueprint.route('/registry/<prefix>')
def resource(prefix: str):
    """Serve the a Bioregistry entry page."""
    prefix = _normalize_prefix_or_404(prefix, '.' + resource.__name__)
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
        has_terms=bioregistry.has_terms(prefix),
        obo_download=bioregistry.get_obo_download(prefix),
        owl_download=bioregistry.get_owl_download(prefix),
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
    """Resolve a CURIE.

    The following things can make a CURIE unable to resolve:

    1. The prefix is not registered with the Bioregistry
    2. The prefix has a validation pattern and the identifier does not match it
    3. There are no providers available for the URL
    """  # noqa:DAR101,DAR201
    if not bioregistry.normalize_prefix(prefix):
        return render_template('resolve_missing_prefix.html', prefix=prefix, identifier=identifier), 404

    pattern = bioregistry.get_pattern(prefix)
    if pattern and not bioregistry.validate(prefix, identifier):
        return render_template(
            'resolve_invalid_identifier.html', prefix=prefix, identifier=identifier, pattern=pattern,
        ), 404

    url = bioregistry.get_link(prefix, identifier, use_bioregistry_io=False)
    if not url:
        return render_template('resolve_missing_providers.html', prefix=prefix, identifier=identifier), 404
    try:
        # TODO remove any garbage characters?
        return redirect(url)
    except ValueError:  # headers could not be constructed
        return render_template('resolve_disallowed_identifier.html', prefix=prefix, identifier=identifier), 404
