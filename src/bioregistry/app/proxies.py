"""Proxies for the web application."""

from flask import current_app
from werkzeug.local import LocalProxy

from bioregistry.resource_manager import Manager

__all__ = [
    "manager",
]

manager: Manager = LocalProxy(lambda: current_app.manager)
