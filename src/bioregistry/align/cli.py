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
def align():
    """Align all external registries."""
    secho("Aligning MIRIAM")
    MiriamAligner.align()

    secho("Aligning N2T")
    N2TAligner.align()

    secho("Aligning NCBI")
    NcbiAligner.align()

    secho("Aligning OBO Foundry")
    OBOFoundryAligner.align()

    secho("Aligning OLS")
    OLSAligner.align()

    secho("Aligning Wikidata")
    WikidataAligner.align()

    secho("Aligning GO")
    GoAligner.align()

    secho("Aligning BioPortal")
    BioPortalAligner.align()

    secho("Aligning Prefix Commons")
    PrefixCommonsAligner.align()

    secho("Aligning Biolink")
    BiolinkAligner.align()

    secho("Aligning UniProt")
    UniProtAligner.align()


if __name__ == "__main__":
    align()
