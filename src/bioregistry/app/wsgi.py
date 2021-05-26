# -*- coding: utf-8 -*-

"""Web application for the Bioregistry."""

from flasgger import Swagger
from flask import Blueprint, Flask, abort, jsonify, render_template, request
from flask_bootstrap import Bootstrap

import bioregistry
from bioregistry.app.ui import ui_blueprint
from .utils import _autocomplete, _get_identifier, _normalize_prefix_or_404, _search
from ..resolve import get_format_url, normalize_prefix
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
    return jsonify(bioregistry.read_registry())


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


@api_blueprint.route('/collection/')
def collections():
    """Get the collection."""
    return jsonify(bioregistry.read_collections())


@api_blueprint.route('/collection/<identifier>')
def collection(identifier: str):
    """Get the collection."""
    data = bioregistry.get_collection(identifier)
    if not data:
        abort(404, f'Invalid collection: {identifier}')
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


@api_blueprint.route('/context.jsonld')
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
    for arg in request.args.getlist('prefix', type=str):
        for prefix in arg.split(','):
            prefix = normalize_prefix(prefix.strip())
            if prefix is None:
                continue
            fmt = get_format_url(prefix)
            if fmt is None:
                continue
            prefix_map[prefix] = fmt

    return jsonify({
        "@context": prefix_map,
    })


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
        registry_size=len(bioregistry.read_registry()),
        metaregistry_size=len(bioregistry.read_metaregistry()),
        collections_size=len(bioregistry.read_collections()),
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
