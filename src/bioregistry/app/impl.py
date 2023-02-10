"""App builder interface."""

import json
from pathlib import Path
from textwrap import dedent
from typing import TYPE_CHECKING, Any, Mapping, Optional, Union

from flasgger import Swagger
from flask import Flask
from flask_bootstrap import Bootstrap4

from bioregistry import curie_to_str, resource_manager, version

from .api import api_blueprint
from .constants import BIOSCHEMAS
from .ui import ui_blueprint

if TYPE_CHECKING:
    import bioregistry

__all__ = [
    "get_app",
]

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
RESOURCES_SUBHEADER_DEFAULT = dedent(
    """\
    <p style="margin-bottom: 0">
        Anyone can <a href="https://github.com/biopragmatics/bioregistry/issues/new/choose">suggest
        improvements</a>, <a href="https://github.com/biopragmatics/bioregistry/issues/new?labels=\
            New%2CPrefix&template=new-prefix.yml&title=Add+prefix+%5BX%5D">request a new prefix</a>,
             or make pull requests to update the underlying database, which is stored in
        <a href="https://github.com/biopragmatics/bioregistry/blob/main/src/bioregistry/data/bioregistry.json">
            JSON</a> on GitHub where the community can engage in an open review process.
    </p>
    """
)


def get_app(
    manager: Optional["bioregistry.Manager"] = None,
    config: Union[None, str, Path, Mapping[str, Any]] = None,
    first_party: bool = True,
) -> Flask:
    """Prepare the flask application.

    :param manager: A pre-configured manager. If none given, uses the default manager.
    :param config: Additional configuration to be passed to the flask application. See below.
    :param first_party: Set to true if deploying the "canonical" bioregistry instance
    :returns: An instantiated flask application
    :raises ValueError: if there's an issue with the configuration's integrity
    """
    app = Flask(__name__)
    if isinstance(config, (str, Path)):
        with open(config) as file:
            app.config.update(json.load(file))
    elif config is not None:
        app.config.update(config)
    app.config.setdefault("METAREGISTRY_TITLE", "Bioregistry")
    app.config.setdefault("METAREGISTRY_FOOTER", FOOTER_DEFAULT)
    app.config.setdefault("METAREGISTRY_HEADER", HEADER_DEFAULT)
    app.config.setdefault("METAREGISTRY_RESOURCES_SUBHEADER", RESOURCES_SUBHEADER_DEFAULT)
    app.config.setdefault("METAREGISTRY_VERSION", version.get_version())
    app.config.setdefault("METAREGISTRY_EXAMPLE_PREFIX", "chebi")
    app.config.setdefault("METAREGISTRY_EXAMPLE_IDENTIFIER", "138488")
    app.config.setdefault("METAREGISTRY_FIRST_PARTY", first_party)

    app.manager = manager or resource_manager.manager

    if app.config.get("METAREGISTRY_FIRST_PARTY"):
        app.config.setdefault("METAREGISTRY_BIOSCHEMAS", BIOSCHEMAS)

    example_prefix = app.config["METAREGISTRY_EXAMPLE_PREFIX"]
    resource = app.manager.registry.get(example_prefix)
    if resource is None:
        raise ValueError(
            f"{example_prefix} is not available as a prefix. Set a different METAREGISTRY_EXAMPLE_PREFIX"
        )
    if resource.get_example() is None:
        raise ValueError("Must use an example prefix with an example identifier")
    if resource.get_uri_format() is None:
        raise ValueError("Must use an example prefix with a URI format")

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
            "host": app.manager.base_url,
            "tags": [
                {
                    "name": "collections",
                    "externalDocs": {
                        "url": f"{app.manager.base_url}/collection/",
                    },
                },
            ],
        }
    )

    Swagger(app)
    Bootstrap4(app)

    app.register_blueprint(api_blueprint)
    app.register_blueprint(ui_blueprint)

    # Make manager available in all jinja templates
    app.jinja_env.globals.update(manager=app.manager, curie_to_str=curie_to_str)
    return app
