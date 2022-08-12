# -*- coding: utf-8 -*-

"""Web application for the Bioregistry."""

import datetime
import platform
from operator import attrgetter
from textwrap import dedent

from flasgger import Swagger
from flask import Flask, current_app, jsonify, render_template
from flask_bootstrap import Bootstrap4

import bioregistry
from bioregistry import version
from bioregistry.constants import NDEX_UUID

from .api import api_blueprint
from .ui import ui_blueprint
from ..resolve_identifier import get_bioregistry_iri
from ..resource_manager import manager
from ..schema.constants import bioregistry_schema_terms
from ..schema.struct import (
    Registry,
    RegistryGovernance,
    RegistrySchema,
    get_json_schema,
    schema_status_map,
)
from ..schema_utils import _read_contributors

TITLE_DEFAULT = "Bioregistry"
FOOTER_DEFAULT = dedent(
    """\
    Developed with ❤️ by the <a href="https://indralab.github.io">INDRA Lab</a> in the
    <a href="https://hits.harvard.edu">Harvard Program in Therapeutic Science (HiTS)</a>.<br/>
    Funded by the DARPA Young Faculty Award W911NF2010255 (PI: Benjamin M. Gyori).<br/>
    Point of contact: <a href="https://github.com/cthoyt">@cthoyt</a>.
    (<a href="https://github.com/biopragmatics/bioregistry">Source code</a>)
"""
)
HEADER_DEFAULT = dedent(
    """\
    <p class="lead">
        The Bioregistry is an open source, community curated registry, meta-registry, and compact
        identifier resolver. Here's what that means:
    </p>
    <dl class="row">
        <dt class="col-lg-2 text-right text-nowrap">Registry</dt>
        <dd class="col-lg-10">
            A collection of prefixes and metadata for ontologies, controlled vocabularies, and other semantic
            spaces. Some other well-known registries are the <a href="http://www.obofoundry.org/">OBO Foundry</a>,
            <a href="https://identifiers.org">Identifiers.org</a>, and the
            the <a href="https://www.ebi.ac.uk/ols/index">OLS</a>.
        </dd>
        <dt class="col-lg-2 text-right text-nowrap">Metaregistry</dt>
        <dd class="col-lg-10">
            A collection of metadata about registries and mappings between their constituent prefixes. For
            example, <a href="https://www.ebi.ac.uk/chebi">ChEBI</a> appears in all of the example registries
            from above. So far, the Bioregistry is the <i>only</i> metaregistry.
        </dd>
        <dt class="col-lg-2 text-right text-nowrap">Resolver</dt>
        <dd class="col-lg-10">
            A tool for mapping compact URIs (CURIEs) of the form <code>prefix:identifier</code> to HTML and
            structured content providers. Some other well-known resolvers are
            <a href="https://identifiers.org">Identifiers.org</a> and <a href="https://n2t.net/">Name-To-Thing</a>.
        </dd>
        <dt class="col-lg-2 text-right text-nowrap">Open Source</dt>
        <dd class="col-lg-10">
            Anyone can <a href="https://github.com/biopragmatics/bioregistry/issues/new/choose">suggest
            improvements</a> or make pull requests to update the underlying database, which is stored in
            <a href="https://github.com/biopragmatics/bioregistry/blob/main/src/bioregistry/data/bioregistry.json">
                JSON</a> on GitHub where the community can engage in an open review process.
        </dd>
        <dt class="col-lg-2 text-right text-nowrap">Community</dt>
        <dd class="col-lg-10">
            Governed by public, well-defined
            <a href="https://github.com/biopragmatics/bioregistry/blob/main/docs/CONTRIBUTING.md">contribution
                guidelines</a>,
            <a href="https://github.com/biopragmatics/bioregistry/blob/main/docs/CODE_OF_CONDUCT.md">code of
            conduct</a>, and
            <a href="https://github.com/biopragmatics/bioregistry/blob/main/docs/GOVERNANCE.md">project
                governance</a> to promote the project's inclusivity and longevity.
        </dd>
    </dl>
"""
)


app = Flask(__name__)
app.manager = manager
app.config.update(
    {
        "METAREGISTRY_TITLE": "ASKEM-Registry",
        "METAREGISTRY_VERSION": version.get_version(),
        "METAREGISTRY_FIRST_PARTY": False,
    }
)
app.config.setdefault("METAREGISTRY_TITLE", "Bioregistry")
app.config.setdefault("METAREGISTRY_HOST", "bioregistry.io")
app.config.setdefault("METAREGISTRY_FOOTER", FOOTER_DEFAULT)
app.config.setdefault("METAREGISTRY_FIRST_PARTY", True)
app.config.setdefault("METAREGISTRY_HEADER", HEADER_DEFAULT)
Swagger.DEFAULT_CONFIG.update(
    {
        "info": {
            "title": app.config["METAREGISTRY_TITLE"],
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
        "host": app.config["METAREGISTRY_HOST"],
        "tags": [
            {
                "name": "collections",
                "externalDocs": {
                    "url": f"https://{app.config['SERVER_NAME']}/collection/",
                },
            },
        ],
    }
)
Swagger(app)
Bootstrap4(app)

app.register_blueprint(api_blueprint)
app.register_blueprint(ui_blueprint)

# Make bioregistry available in all jinja templates
app.jinja_env.globals.update(bioregistry=bioregistry, manager=manager)


@app.route("/")
def home():
    """Render the homepage."""
    example_prefix, example_identifier = "chebi", "138488"
    example_url = manager.get_bioregistry_iri(example_prefix, example_identifier)
    return render_template(
        "home.html",
        example_url=example_url,
        example_prefix=example_prefix,
        example_identifier=example_identifier,
        registry_size=len(manager.registry),
        metaregistry_size=len(manager.metaregistry),
        collections_size=len(manager.collections),
        contributors_size=len(
            _read_contributors(
                registry=manager.registry,
                metaregistry=manager.metaregistry,
                collections=manager.collections,
                contexts=manager.contexts,
            )
        ),
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
        mapping_counts=bioregistry.count_mappings(),
        registries=sorted(bioregistry.read_metaregistry().values(), key=attrgetter("name")),
        schema_status_map=schema_status_map,
        registry_cls=Registry,
        registry_governance_cls=RegistryGovernance,
        registry_schema_cls=RegistrySchema,
    )


@app.route("/download")
def download():
    """Render the download page."""
    return render_template("meta/download.html", ndex_uuid=NDEX_UUID)


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
