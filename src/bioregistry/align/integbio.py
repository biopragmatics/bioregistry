# -*- coding: utf-8 -*-

"""Align Integbio with the Bioregistry."""

from bioregistry.align.utils import Aligner
from bioregistry.external.integbio import get_integbio

__all__ = [
    "IntegbioAligner",
]


class IntegbioAligner(Aligner):
    """Aligner for the Integbio."""

    key = "integbio"
    alt_key_match = "name"
    getter = get_integbio
    curation_header = ("name", "alt_name", "homepage")


if __name__ == "__main__":
    IntegbioAligner.cli()
