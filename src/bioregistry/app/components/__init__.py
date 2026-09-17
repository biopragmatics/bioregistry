"""Components for the UI.

Note that the submodules have to get explicitly imported to make
sure that they are all registered.
"""

from .base import ui_blueprint
from .github_blueprint import github_resolve_issue, github_resolve_pull
from .meta import (
    acknowledgements,
    download,
    funding_manifest_urls,
    highlights_relations,
    schema,
    summary,
    sustainability,
    usage,
)
from .nfdi import show_nfdi
from .resolver import resolve

__all__ = [
    "acknowledgements",
    "download",
    "funding_manifest_urls",
    "github_resolve_issue",
    "github_resolve_pull",
    "highlights_relations",
    "resolve",
    "schema",
    "show_nfdi",
    "summary",
    "sustainability",
    "ui_blueprint",
    "usage",
]
