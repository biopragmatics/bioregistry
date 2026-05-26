"""User-facing endpoints."""

from __future__ import annotations

import datetime
import platform
from operator import attrgetter

import werkzeug
from flask import current_app, render_template

from .base import ui_blueprint
from ..proxies import manager
from ... import version
from ...constants import NDEX_UUID
from ...schema.constants import SCHEMA_TERMS

__all__ = [
    "acknowledgements",
    "download",
    "funding_manifest_urls",
    "highlights_relations",
    "schema",
    "summary",
    "sustainability",
    "usage",
]

_VERSION = version.get_version()
_GIT_HASH = version.get_git_hash()
_PLATFORM = platform.platform()
_PLATFORM_VERSION = platform.version()
_PYTHON_VERSION = platform.python_version()
_DEPLOYED = datetime.datetime.now()


@ui_blueprint.route("/sustainability")
def sustainability() -> str:
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


@ui_blueprint.route("/usage")
def usage() -> str:
    """Render the programmatic usage page."""
    resource = manager.get_resource(current_app.config["METAREGISTRY_EXAMPLE_PREFIX"])
    return render_template("meta/access.html", resource=resource)


@ui_blueprint.route("/.well-known/funding-manifest-urls")
def funding_manifest_urls() -> werkzeug.Response:
    """Render the FLOSS Fund page, described by https://floss.fund/funding-manifest/."""
    return current_app.send_static_file("funding-manifest-urls.txt")


@ui_blueprint.route("/schema/")
def schema() -> str:
    """Render the RDF schema."""
    return render_template("meta/schema.html", terms=SCHEMA_TERMS)


@ui_blueprint.route("/summary")
def summary() -> str:
    """Render the summary page."""
    return render_template("meta/summary.html")


@ui_blueprint.route("/download")
def download() -> str:
    """Render the download page."""
    return render_template("meta/download.html", ndex_uuid=NDEX_UUID)


@ui_blueprint.route("/acknowledgements")
def acknowledgements() -> str:
    """Render the acknowledgements page."""
    return render_template(
        "meta/acknowledgements.html",
        registries=sorted(manager.metaregistry.values(), key=attrgetter("name")),
    )


@ui_blueprint.route("/highlights/relations")
def highlights_relations() -> str:
    """Render the relations highlights page."""
    return render_template("highlights/relations.html")
