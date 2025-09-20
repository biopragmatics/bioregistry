"""Web command for running the app."""

from __future__ import annotations

from pathlib import Path

import click
from more_click import host_option, port_option, verbose_option, with_gunicorn_option

__all__ = [
    "web",
]


@click.command()
@host_option  # type:ignore
@port_option  # type:ignore
@with_gunicorn_option  # type:ignore
@click.option(
    "--workers",
    type=int,
    help="Number of workers",
)
@verbose_option  # type:ignore
@click.option("--registry", type=Path, help="Path to a local registry file")
@click.option("--metaregistry", type=Path, help="Path to a local metaregistry file")
@click.option("--collections", type=Path, help="Path to a local collections file")
@click.option("--contexts", type=Path, help="Path to a local contexts file")
@click.option("--config", type=Path, help="Path to a configuration file")
@click.option("--analytics", is_flag=True)
@click.option(
    "--base-url",
    type=str,
    default="https://bioregistry.io",
    show_default=True,
    help="Base URL for app",
)
def web(
    host: str,
    port: str,
    with_gunicorn: bool,
    workers: int | None,
    registry: Path | None,
    metaregistry: Path | None,
    collections: Path | None,
    contexts: Path | None,
    config: Path | None,
    base_url: str | None,
    analytics: bool,
) -> None:
    """Run the web application."""
    import uvicorn

    from .impl import get_app
    from ..resource_manager import Manager

    if with_gunicorn:
        click.secho("--with-gunicorn is deprecated", fg="yellow")

    manager = Manager(
        registry=registry,
        metaregistry=metaregistry,
        collections=collections,
        contexts=contexts,
        # is being able to load custom mismatches necessary?
        base_url=base_url,
    )
    app = get_app(
        manager=manager,
        config=config,
        first_party=registry is None
        and metaregistry is None
        and collections is None
        and contexts is None,
        return_flask=False,
        analytics=analytics,
    )
    uvicorn.run(app, host=host, port=int(port), workers=workers)
