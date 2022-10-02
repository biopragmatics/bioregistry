# -*- coding: utf-8 -*-

"""Align the OBO Foundry with the Bioregistry."""

from typing import Mapping

from bioregistry.align.utils import Aligner
from bioregistry.external.obofoundry import SKIP, get_obofoundry, get_obofoundry_example

__all__ = [
    "OBOFoundryAligner",
]


class OBOFoundryAligner(Aligner):
    """Aligner for the OBO Foundry."""

    key = "obofoundry"
    getter = get_obofoundry
    curation_header = ("deprecated", "name", "description")
    include_new = True
    normalize_invmap = True

    def get_skip(self) -> Mapping[str, str]:
        """Get the prefixes in the OBO Foundry that should be skipped."""
        return SKIP

    def _align_action(self, bioregistry_id, external_id, external_entry):
        super()._align_action(bioregistry_id, external_id, external_entry)
        if (
            self.manager.get_example(bioregistry_id)
            or self.manager.has_no_terms(bioregistry_id)
            or self.manager.is_deprecated(bioregistry_id)
        ):
            return
        example = get_obofoundry_example(external_id)
        if example:
            self.internal_registry[bioregistry_id]["example"] = example


if __name__ == "__main__":
    OBOFoundryAligner.cli()
