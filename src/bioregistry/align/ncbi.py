# -*- coding: utf-8 -*-

"""Align NCBI with the Bioregistry."""

from typing import Any, Dict, List

from bioregistry.align.utils import Aligner
from bioregistry.external.ncbi import get_ncbi

__all__ = ["NcbiAligner"]


class NcbiAligner(Aligner):
    key = "ncbi"
    getter = get_ncbi
    curation_header = ("name", "generic_urls", "example")

    def prepare_external(
        self, external_id: str, external_entry: Dict[str, str]
    ) -> Dict[str, Any]:
        return external_entry

    def get_curation_row(self, external_id, external_entry) -> List[str]:
        return [
            external_entry["name"],
            external_entry.get("generic_urls"),
            external_entry.get("example"),
        ]


if __name__ == "__main__":
    NcbiAligner.align()
