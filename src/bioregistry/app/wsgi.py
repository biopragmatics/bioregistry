# -*- coding: utf-8 -*-

"""Web application for the Bioregistry."""

from flasgger import Swagger
from flask import Blueprint, Flask, abort, jsonify, redirect, url_for

import bioregistry

app = Flask(__name__)
Swagger.DEFAULT_CONFIG.update({
    'title': 'Bioregistry API',
    'description': 'A service for resolving CURIEs',
    'contact': {
        'responsibleDeveloper': 'Charles Tapley Hoyt',
        'email': 'cthoyt@gmail.com',
    },
    'version': '1.0',
})
Swagger(app)

api_blueprint = Blueprint('api', __name__)


@api_blueprint.route('/registry/')
def get_entries():
    """List the entire Bioregistry."""
    return jsonify(bioregistry.read_bioregistry())


@api_blueprint.route('/registry/<prefix>')
def get_entry(prefix: str):
    """Get an entry.

    ---
    parameters:
    - name: prefix
      in: path
      description: The prefix for the entry
      required: true
      type: string
      example: doid
    """  # noqa:DAR101,DAR201
    entry = bioregistry.get(prefix)
    if entry is None:
        return abort(404)
    return jsonify(entry)


def _get_identifier(prefix, identifier):
    norm_prefix = bioregistry.normalize_prefix(prefix)
    if norm_prefix is None:
        return abort(404, f'invalid prefix: {prefix}')
    if not bioregistry.validate(prefix, identifier):
        return abort(404, f'invalid identifier: {prefix}:{identifier} for pattern {bioregistry.get_pattern(prefix)}')
    providers = bioregistry.get_providers(prefix, identifier)
    if not providers:
        return abort(404, f'no providers available for {prefix}:{identifier}')

    return dict(
        query=dict(prefix=prefix, identifier=identifier),
        providers=providers,
    )


@api_blueprint.route('/registry/<prefix>/<identifier>')
@api_blueprint.route('/registry/<prefix>:<identifier>')
def get_identifier(prefix: str, identifier: str):
    """Look up information on the CURIE.

    ---
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
    """  # noqa:DAR101,DAR201
    return jsonify(_get_identifier(prefix, identifier))


def _get_best_url(d):
    return d['url']


@api_blueprint.route('/resolve/<prefix>/<identifier>')
@api_blueprint.route('/resolve/<prefix>:<identifier>')
def resolve(prefix: str, identifier: str):
    """Resolve the CURIE.

    ---
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
    """  # noqa:DAR101,DAR201
    d = _get_identifier(prefix, identifier)
    return redirect(_get_best_url(d))


app.register_blueprint(api_blueprint)


@app.route('/')
def home():
    """Render the home page."""
    example_prefix, example_id = 'chebi', '24867'
    entries_url = url_for('api.get_entries')
    prefix_url = url_for('api.get_entry', prefix='chebi')
    identifier_url = url_for('api.get_identifier', prefix=example_prefix, identifier=example_id)
    resolve_url = url_for('api.resolve', prefix=example_prefix, identifier=example_id)
    swagger_url = url_for('flasgger.apidocs')

    return f"""
    <h1>Bioregistry Resolver</h1>
    <ul>
    <li><a href={swagger_url}>Swagger UI</a></li>
    <li>Get registry <a href={entries_url}>{entries_url}</a></li>
    <li>Get entry for ChEBI  <a href={prefix_url}>{prefix_url}</a></li>
    <li>Get URLs for ChEBI entry  <a href={identifier_url}>{identifier_url}</a></li>
    <li>Resolve ChEBI entry  <a href={resolve_url}>{example_prefix}:{example_id}</a></li>
    </ul>
    """


if __name__ == '__main__':
    app.run(debug=True)  # noqa
