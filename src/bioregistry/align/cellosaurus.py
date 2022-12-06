# -*- coding: utf-8 -*-

"""Align Cellosaurus with the Bioregistry."""

from typing import Mapping

from bioregistry.align.utils import Aligner
from bioregistry.constants import URI_FORMAT_KEY
from bioregistry.external.cellosaurus import get_cellosaurus

__all__ = [
    "CellosaurusAligner",
]


class CellosaurusAligner(Aligner):
    """Aligner for the Cellosaurus."""

    key = "cellosaurus"
    getter = get_cellosaurus
    curation_header = ("name", "homepage", "category", URI_FORMAT_KEY)

    def get_skip(self) -> Mapping[str, str]:
        """Get the skipped Cellosaurus identifiers."""
        return {
            "CCTCC": "dead site",
            "CCLV": "stub website, URL dead",
        }


if __name__ == "__main__":
    CellosaurusAligner.cli()
