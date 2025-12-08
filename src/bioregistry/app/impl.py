"""App builder interface."""

from __future__ import annotations

import json
from pathlib import Path
from textwrap import dedent
from typing import Any, Literal, cast, overload

import pystow
from a2wsgi import WSGIMiddleware
from curies.mapping_service import MappingServiceGraph, MappingServiceSPARQLProcessor
from fastapi import APIRouter, FastAPI
from flask import Flask
from flask_bootstrap import Bootstrap4
from markdown import markdown
from rdflib_endpoint.sparql_router import SparqlRouter

from .api import api_router
from .constants import BIOSCHEMAS, KEY_A, KEY_B, KEY_C, KEY_D, KEY_E
from .ui import ui_blueprint
from .. import resource_manager, version
from ..constants import (
    INTERNAL_DOCKERHUB_SLUG,
    INTERNAL_MASTODON,
    INTERNAL_MASTODON_HANDLE,
    INTERNAL_MASTODON_SERVER,
    INTERNAL_PIP,
    INTERNAL_REPOSITORY,
    INTERNAL_REPOSITORY_BLOB,
    INTERNAL_REPOSITORY_PAGES,
    INTERNAL_REPOSITORY_RAW,
    INTERNAL_REPOSITORY_SLUG,
    POWERED_BY_BIOREGISTRY_IMAGE,
    SCHEMA_CURIE_PREFIX,
    SCHEMA_URI_PREFIX,
)
from ..resource_manager import Manager
from ..utils import curie_to_str

__all__ = [
    "get_app",
]


BIOREGISTRY_TITLE_DEFAULT = "Bioregistry"
BIOREGISTRY_DESCRIPTION_DEFAULT = dedent("""\
    An open source, community curated registry, meta-registry,
    and compact identifier (CURIE) resolver.
""")
BIOREGISTRY_FOOTER_DEFAULT = dedent(f"""\
    <div class="row mt-3"><h5>Projects and Partners</h3></div>
    <div class="row mt-2">
        <div class="col text-center align-self-center"><a href="https://www.iac.rwth-aachen.de"><img src="/static/rwth-iac.svg" style="height: 2.3em;" /></a></div>
        <div class="col text-center align-self-center"><a href="https://nfdi4chem.de"><img src="/static/nfdi4chem.svg" style="height: 2.3em;" /></a></div>
        <div class="col text-center align-self-center"><a href="https://dalia.education/en"><img src="/static/dalia.png" style="height: 1.9em;" /></a></div>
        <div class="col text-center align-self-center"><a href="https://www.northeastern.edu"><img src="/static/northeastern.svg" style="height: 2.3em;" /></a></div>
    </div>
    <div class="row mt-4"><h5>Funding</h3></div>
    <div class="row mt-1">
        <div class="col text-center align-self-center"><a href="https://www.dfg.de"><img src="/static/dfg.svg" style="height: 2.3em;" /></a></div>
        <div class="col text-center align-self-center"><a href="https://chanzuckerberg.com"><img src="/static/czi.svg" style="height: 3.5em;" /></a></div>
        <div class="col text-center align-self-center"></div>
        <div class="col text-center align-self-center"></div>
    </div>

    <hr class="mt-5 mb-4"/>

    <p class="small text-center text-muted">
    Developed with ❤️ by the
    <a href="https://www.iac.rwth-aachen.de">Institute for Inorganic Chemistry</a> at RWTH Aachen University
    </br> and the
    <a href="https://gyorilab.github.io">Gyori Lab for Computational Biomedicine</a>
    at Northeastern University.<br/>
    Point of contact: Charles Tapley Hoyt (<a href="https://github.com/cthoyt">@cthoyt</a>; RWTH Aachen)
    </p>

    <div class="text-center">
    <a class="btn btn-outline-primary btn-sm mb-1" rel="me" href="https://{INTERNAL_MASTODON_SERVER}/@{INTERNAL_MASTODON_HANDLE}" title="{INTERNAL_MASTODON_HANDLE}"> @{INTERNAL_MASTODON}</a>
    <a class="btn btn-outline-primary btn-sm mb-1" href="{INTERNAL_REPOSITORY}"><i class="fa fa-brands fa-github"></i> Source Code</a>
    </div>
""")
BIOREGISTRY_HEADER_DEFAULT = dedent("""\
    <p class="lead">
        The Bioregistry is an open source, community curated registry, meta-registry, and compact
        identifier resolver. Here's what that means:
    </p>
    <dl class="row">
        <dt class="col-lg-2 text-right text-nowrap">Registry</dt>
        <dd class="col-lg-10">
            A collection of prefixes and metadata for ontologies, controlled vocabularies, and other semantic
            spaces. Some other well-known registries are the <a href="http://www.obofoundry.org/">OBO Foundry</a>,
            <a href="https://identifiers.org">Identifiers.org</a>, and
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
""")
RESOURCES_SUBHEADER_DEFAULT = dedent("""\
    <p style="margin-bottom: 0">
        Anyone can <a href="https://github.com/biopragmatics/bioregistry/issues/new/choose">suggest
        improvements</a>, <a href="https://github.com/biopragmatics/bioregistry/issues/new?labels=\
            New%2CPrefix&template=new-prefix.yml&title=Add+prefix+%5BX%5D">request a new prefix</a>,
             or make pull requests to update the underlying database, which is stored in
        <a href="https://github.com/biopragmatics/bioregistry/blob/main/src/bioregistry/data/bioregistry.json">
            JSON</a> on GitHub where the community can engage in an open review process.
    </p>
""")
BIOREGISTRY_HARDWARE_DEFAULT = dedent("""\
The Bioregistry is hosted on an Amazon Elastic Compute Cloud (EC2) via a load balancing service to stay secure
and highly available.
It is managed and supported by the <a href="https://gyorilab.github.io/">Gyori Lab for Computational
Biomedicine</a> at Northeastern University.
""")
BIOREGISTRY_CITATION_TEXT = dedent("""\
<h2>Citing the Bioregistry</h2>
<p>
    This web application is built on top of the Bioregistry, which can be cited with the following:
    <blockquote class="blockquote">
        Hoyt, C. T., <i>et al.</i> (2022) <a href="https://bioregistry.io/doi:10.1038/s41597-022-01807-3">The
        Unifying the identification of biomedical entities with the Bioregistry</a>. <i>Scientific Data</i>,
        s41597-022-01807-3
    </blockquote>
</p>
<p>or by using the following LaTeX:</p>
<pre><code class="language-bibtex">@article{Hoyt2022Bioregistry,
    author  = {Hoyt, Charles Tapley and Balk, Meghan and Callahan, Tiffany J and Domingo-Fern{\'{a}}ndez, Daniel and Haendel, Melissa A and Hegde, Harshad B and Himmelstein, Daniel S and Karis, Klas and Kunze, John and Lubiana, Tiago and Matentzoglu, Nicolas and McMurry, Julie and Moxon, Sierra and Mungall, Christopher J and Rutz, Adriano and Unni, Deepak R and Willighagen, Egon and Winston, Donald and Gyori, Benjamin M},
    doi     = {10.1038/s41597-022-01807-3},
    issn    = {2052-4463},
    journal = {Sci. Data},
    number  = {1},
    pages   = {714},
    title   = {Unifying the identification of biomedical entities with the Bioregistry},
    url     = {https://doi.org/10.1038/s41597-022-01807-3},
    volume  = {9},
    year    = {2022}
}</code></pre>
""")
BIOREGISTRY_BADGE_BLOCK = dedent(f"""\
<h2>Bioregistry Badge</h2>
<p>
    If you use the Bioregistry in your code, support us by including our
    badge in your project's README.md:
</p>
<pre><code class="language-markdown">[![Powered by the Bioregistry](https://img.shields.io/static/v1?label=Powered%20by&message=Bioregistry&color=BA274A&style=flat&logo={POWERED_BY_BIOREGISTRY_IMAGE})](https://github.com/biopragmatics/bioregistry)
</code></pre>

<p>If you've got README.rst, use this instead:</p>
<pre><code class="language-rest">.. image:: https://img.shields.io/static/v1?label=Powered%20by&message=Bioregistry&color=BA274A&style=flat&logo={POWERED_BY_BIOREGISTRY_IMAGE}
:target: https://github.com/biopragmatics/bioregistry
:alt: Powered by the Bioregistry</code></pre>

<p>Including in your website in HTML:</p>
<pre><code class="language-html">&lt;a href="https://github.com/biopragmatics/bioregistry"$&gt;
&lt;img alt="Powered by the Bioregistry" src="https://img.shields.io/static/v1?label=Powered%20by&message=Bioregistry&color=BA274A&style=flat&logo={POWERED_BY_BIOREGISTRY_IMAGE}" /&gt;
&lt;/a&gt;</code></pre>

<p>
    It looks like this <a href="https://github.com/biopragmatics/bioregistry">
    <img alt="Powered by the Bioregistry"
         src="https://img.shields.io/static/v1?label=Powered%20by&message=Bioregistry&color=BA274A&style=flat&logo={POWERED_BY_BIOREGISTRY_IMAGE}"/>
</a>
</p>
""")
BIOREGISTRY_DEPLOYMENT_BLOCK = dedent(f"""\
<h3>Containerization</h3>
<p>
    A Docker image is automatically built weekly following the
    <a href="{INTERNAL_REPOSITORY}/actions/workflows/update.yml">update workflow</a>
    on GitHub Actions and pushed to the <a href="https://hub.docker.com/r/{INTERNAL_DOCKERHUB_SLUG}"><i class="fab fa-docker"></i>
    {INTERNAL_DOCKERHUB_SLUG}</a> DockerHub repository. This image is built with the Python 3.9 alpine base image,
    which significantly reduces non-essential components. The final compressed image weights less than 40 MB of disk
    space and runs inside Docker with about 65 MB of memory at baseline. This could easily fit on a dedicated
    <a href="https://aws.amazon.com/ec2/instance-types/t4/">t4g.nano</a> instance on AWS that costs about
    $37/year on-demand or around $20/year reserved.
</p>

<h3>Deployment</h3>
<p>
    The Bioregistry's EC2 instance runs the following script on a cron job that stops the current running instance,
    pulls the latest image from this DockerHub repository and starts it back up. The whole process only takes a few
    seconds.
</p>
<pre><code class="language-bash">#!/bin/bash
# /data/services/restart_bioregistry.sh

# Store the container's hash
BIOREGISTRY_CONTAINER_ID=$(docker ps --filter "name=bioregistry" -aq)

# Stop and remove the old container, taking advantage of the fact that it's named specifically
if [ -n "BIOREGISTRY_CONTAINER_ID" ]; then
docker stop $BIOREGISTRY_CONTAINER_ID
docker rm $BIOREGISTRY_CONTAINER_ID
fi

# Pull the latest
docker pull biopragmatics/bioregistry:latest

# Run the start script, remove -d to run interactively
docker run -id --name bioregistry -p 8766:8766 biopragmatics/bioregistry:latest</code></pre>
<p>This script can be put on the EC2 instance and run via SSH with:</p>
<pre><code class="language-bash">#!/bin/bash

ssh -i ~/.ssh/&lt;credentials&gt.pem &lt;user&gt;@&lt;address&gt; 'sh /data/services/restart_bioregistry.sh'</code></pre>
<h3>SSL/TLS</h3>
<p>
    The SSL/TLS certificate for <code>bioregistry.io</code> so it can be served with HTTPS is managed through
    the <a href="https://aws.amazon.com/certificate-manager/">AWS Certificate Manager</a>.
</p>
""")

BIOREGISTRY_DOMAIN_NAME_BLOCK = dedent("""\
<h3>Domain Name</h3>
<p>
    The <code>bioregistry.io</code> domain is registered with Namecheap and costs about $33 per year. It is managed
    and supported by the <a
        href="https://gyorilab.github.io/">Gyori Lab for Computational Biomedicine</a> at Northeastern University.
</p>
""")


# docstr-coverage:excused `overload`
@overload
def get_app(
    manager: Manager | None = ...,
    config: None | str | Path | dict[str, Any] = ...,
    *,
    first_party: bool = ...,
    return_flask: Literal[True] = True,
    analytics: bool = ...,
    import_name: str | None = ...,
    flask_kwargs: dict[str, Any] | None = ...,
) -> tuple[FastAPI, Flask]: ...


# docstr-coverage:excused `overload`
@overload
def get_app(
    manager: Manager | None = ...,
    config: None | str | Path | dict[str, Any] = ...,
    *,
    first_party: bool = ...,
    return_flask: Literal[False] = False,
    analytics: bool = ...,
    import_name: str | None = ...,
    flask_kwargs: dict[str, Any] | None = ...,
) -> FastAPI: ...


def get_app(
    manager: Manager | None = None,
    config: None | str | Path | dict[str, Any] = None,
    *,
    first_party: bool = True,
    return_flask: bool = False,
    analytics: bool = False,
    import_name: str | None = None,
    flask_kwargs: dict[str, Any] | None = None,
) -> FastAPI | tuple[FastAPI, Flask]:
    """Prepare the WSGI application.

    :param manager: A pre-configured manager. If none given, uses the default manager.
    :param config: Additional configuration to be passed to the flask application. See
        below.
    :param first_party: Set to true if deploying the "canonical" bioregistry instance
    :param return_flask: Set to true to get internal flask app
    :param analytics: Should analytics be enabled?
    :param import_name: The import name for the flask app
    :param flask_kwargs: Remaining keyword arguments to pass to the flask app
        (don't pass ``import_name`` as a key here)

    :returns: An instantiated WSGI application

    :raises ValueError: if there's an issue with the configuration's integrity
    """
    app = Flask(import_name=import_name or __name__, **(flask_kwargs or {}))

    if manager is None:
        manager = resource_manager.manager

    conf = _prepare_config(config, first_party)
    example_prefix = conf["METAREGISTRY_EXAMPLE_PREFIX"]
    resource = manager.get_resource(example_prefix, strict=True)
    if resource.get_example() is None:
        raise ValueError("Must use an example prefix with an example identifier")
    if resource.get_uri_format() is None:
        raise ValueError("Must use an example prefix with a URI format")

    # note from klas:
    # "host": removeprefix(removeprefix(manager.base_url, "https://"), "http://"),

    Bootstrap4(app)

    app.register_blueprint(ui_blueprint)

    app.config.update(conf)
    app.manager = manager

    if app.config.get("METAREGISTRY_FIRST_PARTY"):
        app.config.setdefault("METAREGISTRY_BIOSCHEMAS", BIOSCHEMAS)

    fast_api = FastAPI(
        openapi_tags=_get_tags_metadata(conf, manager),
        title=conf["METAREGISTRY_TITLE"],
        description=conf["METAREGISTRY_DESCRIPTION"],
        contact={
            "name": conf["METAREGISTRY_CONTACT_NAME"],
            "email": conf["METAREGISTRY_CONTACT_EMAIL"],
        },
        license_info={
            "name": conf["METAREGISTRY_LICENSE_NAME"],
            "url": conf["METAREGISTRY_LICENSE_URL"],
        },
    )
    fast_api.manager = manager  # type:ignore
    fast_api.include_router(api_router)
    fast_api.include_router(_get_sparql_router(app))
    fast_api.mount("/", WSGIMiddleware(app))  # type:ignore

    # yes, this isn't very secure. just for testing now.
    key = "-".join([KEY_A, KEY_B, KEY_C, KEY_D, KEY_E])
    analytics_api_key = conf.get("ANALYTICS_API_KEY") or pystow.get_config(
        "bioregistry",
        "analytics_api_key",
        passthrough=key,
    )
    if analytics_api_key and analytics:
        from api_analytics.fastapi import Analytics

        fast_api.add_middleware(Analytics, api_key=analytics_api_key)  # Add middleware

    # Make manager available in all jinja templates
    app.jinja_env.globals.update(
        manager=manager,
        curie_to_str=curie_to_str,
        fastapi_url_for=fast_api.url_path_for,
        markdown=markdown,
    )

    if return_flask:
        return fast_api, app
    return fast_api


def _prepare_config(
    config: None | str | Path | dict[str, Any] = None, first_party: bool = True
) -> dict[str, Any]:
    if isinstance(config, str | Path):
        with open(config) as file:
            config = cast(dict[str, Any], json.load(file))
    elif config is None:
        config = {}

    config.setdefault("METAREGISTRY_FIRST_PARTY", first_party)
    config.setdefault("METAREGISTRY_CONTACT_NAME", "Charles Tapley Hoyt")
    config.setdefault("METAREGISTRY_CONTACT_EMAIL", "cthoyt@gmail.com")
    config.setdefault("METAREGISTRY_LICENSE_NAME", "MIT License")
    config.setdefault("METAREGISTRY_VERSION", version.get_version())
    config.setdefault("METAREGISTRY_EXAMPLE_PREFIX", "chebi")
    config.setdefault("METAREGISTRY_EXAMPLE_IDENTIFIER", "138488")
    config.setdefault("METAREGISTRY_LICENSE_URL", f"{INTERNAL_REPOSITORY_BLOB}/LICENSE")
    config.setdefault("METAREGISTRY_DOCKERHUB_SLUG", INTERNAL_DOCKERHUB_SLUG)
    config.setdefault("METAREGISTRY_REPOSITORY_SLUG", INTERNAL_REPOSITORY_SLUG)
    config.setdefault("METAREGISTRY_REPOSITORY", INTERNAL_REPOSITORY)
    config.setdefault("METAREGISTRY_REPOSITORY_PAGES", INTERNAL_REPOSITORY_PAGES)
    config.setdefault("METAREGISTRY_REPOSITORY_RAW", INTERNAL_REPOSITORY_RAW)
    config.setdefault("METAREGISTRY_PYTHON_PACKAGE", INTERNAL_PIP)
    config.setdefault("METAREGISTRY_CITATION", BIOREGISTRY_CITATION_TEXT)
    config.setdefault("METAREGISTRY_BADGE_BLOCK", BIOREGISTRY_BADGE_BLOCK)
    config.setdefault("METAREGISTRY_MASTODON", INTERNAL_MASTODON)
    config.setdefault("METAREGISTRY_SCHEMA_PREFIX", SCHEMA_CURIE_PREFIX)
    config.setdefault("METAREGISTRY_SCHEMA_URI_PREFIX", SCHEMA_URI_PREFIX)
    config.setdefault("METAREGISTRY_RESOURCES_SUBHEADER", RESOURCES_SUBHEADER_DEFAULT)

    # key for updating on non-first party
    config.setdefault("METAREGISTRY_TITLE", BIOREGISTRY_TITLE_DEFAULT)
    config.setdefault("METAREGISTRY_DESCRIPTION", BIOREGISTRY_DESCRIPTION_DEFAULT)
    config.setdefault("METAREGISTRY_FOOTER", BIOREGISTRY_FOOTER_DEFAULT)
    config.setdefault("METAREGISTRY_HEADER", BIOREGISTRY_HEADER_DEFAULT)
    config.setdefault("METAREGISTRY_HARDWARE", BIOREGISTRY_HARDWARE_DEFAULT)

    # should not be there if not first-party
    config.setdefault("METAREGISTRY_DEPLOYMENT", BIOREGISTRY_DEPLOYMENT_BLOCK)
    config.setdefault("METAREGISTRY_DOMAIN_NAME_BLOCK", BIOREGISTRY_DOMAIN_NAME_BLOCK)

    return config


example_query = """\
PREFIX owl: <http://www.w3.org/2002/07/owl#>

SELECT ?s ?o WHERE {
    VALUES ?s { <http://purl.obolibrary.org/obo/CHEBI_1> }
    ?s owl:sameAs ?o
}
""".rstrip()


def _get_sparql_router(app: Flask) -> APIRouter:
    sparql_graph = MappingServiceGraph(converter=app.manager.converter)
    sparql_processor = MappingServiceSPARQLProcessor(graph=sparql_graph)
    sparql_router: APIRouter = SparqlRouter(
        path="/sparql",
        title=f"{app.config['METAREGISTRY_TITLE']} SPARQL Service",
        description="An identifier mapping service",
        version=version.get_version(),
        example_query=example_query,
        graph=sparql_graph,
        processor=sparql_processor,
        public_url=f"{app.manager.base_url}/sparql",
    )
    return sparql_router


def _get_tags_metadata(conf: dict[str, str], manager: Manager) -> list[dict[str, Any]]:
    tags_metadata = [
        {
            "name": "resource",
            "description": "Identifier resources in the registry",
            "externalDocs": {
                "description": f"{conf['METAREGISTRY_TITLE']} Resource Catalog",
                "url": f"{manager.base_url}/registry/",
            },
        },
        {
            "name": "metaresource",
            "description": "Resources representing registries",
            "externalDocs": {
                "description": f"{conf['METAREGISTRY_TITLE']} Registry Catalog",
                "url": f"{manager.base_url}/metaregistry/",
            },
        },
        {
            "name": "collection",
            "description": "Fit-for-purpose lists of prefixes",
            "externalDocs": {
                "description": f"{conf['METAREGISTRY_TITLE']} Collection Catalog",
                "url": f"{manager.base_url}/collection/",
            },
        },
    ]
    return tags_metadata
