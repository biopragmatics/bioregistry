"""Proxies for the web application."""

from typing import cast

from flask import current_app
from werkzeug.local import LocalProxy

from bioregistry.resource_manager import Manager

__all__ = [
    "manager",
]

manager: Manager = cast(Manager, LocalProxy(lambda: current_app.manager))
