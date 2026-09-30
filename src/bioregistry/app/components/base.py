"""The base for the UI blueprint."""

from __future__ import annotations

from flask import Blueprint

from ..constants import TEMPLATES_DIRECTORY

__all__ = ["ui_blueprint"]

ui_blueprint = Blueprint(
    "metaregistry_ui", __name__, template_folder=TEMPLATES_DIRECTORY.as_posix()
)
