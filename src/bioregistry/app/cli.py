# -*- coding: utf-8 -*-

"""Web command for running the app."""

from pathlib import Path
from typing import Optional

import click
from more_click import (
    flask_debug_option,
    gunicorn_timeout_option,
    host_option,
    port_option,
    run_app,
    verbose_option,
    with_gunicorn_option,
    workers_option,
)

from .impl import get_app
from ..resource_manager import Manager

__all__ = [
    "web",
]


@click.command()
@host_option
@port_option
@with_gunicorn_option
@workers_option
@verbose_option
@gunicorn_timeout_option
@flask_debug_option
@click.option("--registry", type=Path, help="Path to a local registry file")
@click.option("--metaregistry", type=Path, help="Path to a local metaregistry file")
@click.option("--collections", type=Path, help="Path to a local collections file")
@click.option("--contexts", type=Path, help="Path to a local contexts file")
@click.option("--config", type=Path, help="Path to a configuration file")
def web(
    host: str,
    port: str,
    with_gunicorn: bool,
    workers: int,
    debug: bool,
    timeout: Optional[int],
    registry: Optional[Path] = None,
    metaregistry: Optional[Path] = None,
    collections: Optional[Path] = None,
    contexts: Optional[Path] = None,
    config: Optional[Path] = None,
):
    """Run the web application."""
    manager = Manager(
        registry=registry,
        metaregistry=metaregistry,
        collections=collections,
        contexts=contexts,
        # is being able to load custom mismatches necessary?
    )
    app = get_app(
        manager=manager,
        config=config,
    )
    run_app(
        app=app,
        host=host,
        port=port,
        workers=workers,
        with_gunicorn=with_gunicorn,
        debug=debug,
        timeout=timeout,
    )
