"""Web command for running the app."""

from __future__ import annotations

from pathlib import Path

import click
from more_click import host_option, port_option, verbose_option, with_gunicorn_option

from bioregistry.constants import BIOREGISTRY_DEFAULT_BASE_URL

__all__ = [
    "web",
]


@click.command()
@host_option
@port_option
@with_gunicorn_option
@click.option(
    "--workers",
    type=int,
    help="Number of workers",
)
@verbose_option
@click.option("--registry", type=Path, help="Path to a local registry file")
@click.option("--metaregistry", type=Path, help="Path to a local metaregistry file")
@click.option("--collections", type=Path, help="Path to a local collections file")
@click.option("--contexts", type=Path, help="Path to a local contexts file")
@click.option("--config", type=Path, help="Path to a configuration file")
@click.option("--analytics", is_flag=True)
@click.option(
    "--base-url",
    type=str,
    default=BIOREGISTRY_DEFAULT_BASE_URL,
    show_default=True,
    help="Base URL for app",
)
@click.option("--tab", is_flag=True, help="If passed, automatically opens a web browser")
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
    tab: bool,
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
    if tab:
        import webbrowser

        webbrowser.open_new_tab(f"http://{host}:{port}")
    uvicorn.run(app, host=host, port=int(port), workers=workers)
