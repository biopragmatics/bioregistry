# -*- coding: utf-8 -*-

"""Web application for the Bioregistry."""

import datetime
import platform
from operator import attrgetter

from flasgger import Swagger
from flask import Flask, jsonify, render_template
from flask_bootstrap import Bootstrap4

import bioregistry
from bioregistry import version

from .api import api_blueprint
from .ui import ui_blueprint
from ..resolve_identifier import get_bioregistry_iri
from ..schema.constants import bioregistry_schema_terms
from ..schema.struct import get_json_schema, schema_status_map

app = Flask(__name__)
Swagger.DEFAULT_CONFIG.update(
    {
        "info": {
            "title": "Bioregistry",
            "description": "A service for resolving CURIEs",
            "contact": {
                "responsibleDeveloper": "Charles Tapley Hoyt",
                "email": "cthoyt@gmail.com",
            },
            "version": "1.0",
            "license": {
                "name": "Code available under the MIT License",
                "url": "https://github.com/biopragmatics/bioregistry/blob/main/LICENSE",
            },
        },
        "host": "bioregistry.io",
        "tags": [
            {
                "name": "collections",
                "externalDocs": {
                    "url": "https://bioregistry.io/collection/",
                },
            },
        ],
    }
)
Swagger(app)
Bootstrap4(app)

app.register_blueprint(api_blueprint)
app.register_blueprint(ui_blueprint)


@app.route("/")
def home():
    """Render the homepage."""
    example_prefix, example_identifier = "chebi", "138488"
    example_url = get_bioregistry_iri(example_prefix, example_identifier)
    return render_template(
        "home.html",
        example_url=example_url,
        example_prefix=example_prefix,
        example_identifier=example_identifier,
        registry_size=len(bioregistry.read_registry()),
        metaregistry_size=len(bioregistry.read_metaregistry()),
        collections_size=len(bioregistry.read_collections()),
        contributors_size=len(bioregistry.read_contributors()),
    )


@app.route("/summary")
def summary():
    """Render the summary page."""
    return render_template("meta/summary.html")


@app.route("/related")
def related():
    """Render the related page."""
    return render_template(
        "meta/related.html",
        registries=sorted(bioregistry.read_metaregistry().values(), key=attrgetter("name")),
        schema_status_map=schema_status_map,
    )


@app.route("/download")
def download():
    """Render the download page."""
    return render_template("meta/download.html")


@app.route("/acknowledgements")
def acknowledgements():
    """Render the acknowledgements page."""
    return render_template(
        "meta/acknowledgements.html",
        registries=sorted(bioregistry.read_metaregistry().values(), key=attrgetter("name")),
    )


_VERSION = version.get_version()
_GIT_HASH = version.get_git_hash()
_PLATFORM = platform.platform()
_PLATFORM_VERSION = platform.version()
_PYTHON_VERSION = platform.python_version()
_DEPLOYED = datetime.datetime.now()

app.config["bioregistry_version"] = _VERSION


@app.route("/sustainability")
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


@app.route("/usage")
def usage():
    """Render the programmatic usage page."""
    return render_template("meta/access.html")


@app.route("/schema/")
def schema():
    """Render the Bioregistry RDF schema."""
    return render_template("meta/schema.html", terms=bioregistry_schema_terms)


@app.route("/schema.json")
def json_schema():
    """Return the JSON schema."""
    return jsonify(get_json_schema())


if __name__ == "__main__":
    app.run(debug=True)  # noqa
