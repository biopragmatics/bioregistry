# -*- coding: utf-8 -*-

"""Web application for the Bioregistry."""

from flasgger import Swagger
from flask import Blueprint, Flask, abort, jsonify, render_template, request
from flask_bootstrap import Bootstrap

import bioregistry
from bioregistry.app.ui import ui_blueprint
from .utils import _autocomplete, _get_identifier, _normalize_prefix_or_404, _search
from ..resolve_identifier import _get_bioregistry_link

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
Bootstrap(app)

api_blueprint = Blueprint('api', __name__, url_prefix='/api')


@api_blueprint.route('/registry/')
def resources():
    """List the entire Bioregistry."""
    return jsonify(bioregistry.read_bioregistry())


@api_blueprint.route('/metaregistry/')
def metaresources():
    """List the entire Bioregistry metaregistry."""
    return jsonify(bioregistry.read_metaregistry())


@api_blueprint.route('/metaregistry/<metaprefix>')
def metaresource(metaprefix: str):
    """List the registry."""
    data = bioregistry.get_registry(metaprefix)
    if not data:
        abort(404, f'Invalid metaprefix: {metaprefix}')
    return jsonify(data)


@api_blueprint.route('/registry/<prefix>')
def resource(prefix: str):
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
    prefix = _normalize_prefix_or_404(prefix)
    return jsonify(prefix=prefix, **bioregistry.get(prefix))  # type:ignore


@api_blueprint.route('/reference/<prefix>:<identifier>')
def reference(prefix: str, identifier: str):
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


app.register_blueprint(api_blueprint)
app.register_blueprint(ui_blueprint)


@app.route('/')
def home():
    """Render the homepage."""
    example_prefix, example_identifier = 'chebi', '138488'
    example_url = _get_bioregistry_link(example_prefix, example_identifier)
    return render_template(
        'home.html',
        example_url=example_url,
        example_prefix=example_prefix,
        example_identifier=example_identifier,
        registry_size=len(bioregistry.read_bioregistry()),
        metaregistry_size=len(bioregistry.read_metaregistry()),
    )


@app.route('/summary')
def summary():
    """Render the summary page."""
    return render_template('summary.html')


@app.route('/download')
def download():
    """Render the download page."""
    return render_template('download.html')


if __name__ == '__main__':
    app.run(debug=True)  # noqa
