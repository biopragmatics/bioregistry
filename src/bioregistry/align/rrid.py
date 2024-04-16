# -*- coding: utf-8 -*-

"""Align RRID with the Bioregistry."""

from typing import Mapping

from bioregistry.align.utils import Aligner
from bioregistry.external.scicrunch import get_rrid

__all__ = [
    "RRIDAligner",
]


UNCURATABLE = {
    "XEP": "could not find an example entity number",
    "CWRU": "could not find evidence that this is an identifier resource",
    "XGSC": "could not find evidence that this is an identifier resource",
    "SSCLBR": "dead resource",
    "EXRC": "resource does not have stable/referencable identifiers for entities",
    "IMSR": "meta-site that seems to wrap other IMSR sites",
    "IMSR_CARD": "dead website",
    "IMSR_CMMR": "just a wrapper around MGI",
    "IMSR_CRL": "Massive site, too cryptic, can't find",
    "IMSR_GPT": "actual URLs don't match accession numbers",
    "IMSR_HAR": "could not find evidence that this is an identifier resource",
    "IMSR_NM-KI": "multiple conflicting identifiers - actual URLs don't match accession numbers",
    "IMSR_NIG": "could not find evidence that this is an identifier resource",
    "IMSR_TIGM": "could not find evidence that this is an identifier resource",
}


class RRIDAligner(Aligner):
    """Aligner for the RRID."""

    key = "rrid"
    getter = get_rrid
    alt_key_match = "abbreviation"
    curation_header = ("name", "homepage")

    def get_skip(self) -> Mapping[str, str]:
        """Get prefixes to skip."""
        return UNCURATABLE


if __name__ == "__main__":
    RRIDAligner.cli()
