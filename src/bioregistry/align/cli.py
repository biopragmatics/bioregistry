# -*- coding: utf-8 -*-

"""CLI for alignment."""

import click

from .biolink import BiolinkAligner
from .bioportal import BioPortalAligner
from .go import GoAligner
from .miriam import MiriamAligner
from .n2t import N2TAligner
from .ncbi import NcbiAligner
from .obofoundry import OBOFoundryAligner
from .ols import OLSAligner
from .prefix_commons import PrefixCommonsAligner
from .uniprot import UniProtAligner
from .wikidata import WikidataAligner
from ..utils import secho

__all__ = [
    "align",
]


@click.command()
@click.option("--quiet", is_flag=True)
def align(quiet: bool):
    """Align all external registries."""
    for aligner_cls in [
        MiriamAligner,
        N2TAligner,
        NcbiAligner,
        OBOFoundryAligner,
        OLSAligner,
        WikidataAligner,
        GoAligner,
        BioPortalAligner,
        PrefixCommonsAligner,
        BiolinkAligner,
        UniProtAligner,
    ]:
        secho(f"Aligning {aligner_cls.key}")
        try:
            aligner_cls.align(quiet=quiet)
        except IOError:
            secho(f"Failed to align {aligner_cls.key}", fg="red")


if __name__ == "__main__":
    align()
