"""A blueprint for resolving GitHub issues and pull requests."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flask import redirect

from .base import ui_blueprint

if TYPE_CHECKING:
    import werkzeug

__all__ = [
    "github_resolve_issue",
    "github_resolve_pull",
]


@ui_blueprint.route("/resolve/github/issue/<owner>/<repository>/<int:issue>")
def github_resolve_issue(owner: str, repository: str, issue: str) -> werkzeug.Response:
    """Redirect to an issue on GitHub."""
    return redirect(f"https://github.com/{owner}/{repository}/issues/{issue}")


@ui_blueprint.route("/resolve/github/pull/<owner>/<repository>/<int:pull>")
def github_resolve_pull(owner: str, repository: str, pull: int) -> werkzeug.Response:
    """Redirect to a pull request on GitHub."""
    return redirect(f"https://github.com/{owner}/{repository}/pull/{pull}")
