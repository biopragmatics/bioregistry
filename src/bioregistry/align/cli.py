# -*- coding: utf-8 -*-

"""CLI for alignment."""

import click

from .biolink import BiolinkAligner
from .bioportal import BioPortalAligner
from .go import GoAligner
from .miriam import align_miriam
from .n2t import align_n2t
from .ncbi import NcbiAligner
from .obofoundry import align_obofoundry
from .ols import align_ols
from .prefix_commons import PrefixCommonsAligner
from .wikidata import align_wikidata
from ..utils import secho

__all__ = [
    'align',
]


@click.command()
def align():
    """Align all external registries."""
    secho('Aligning MIRIAM')
    align_miriam()

    secho('Aligning N2T')
    align_n2t()

    secho('Aligning NCBI')
    NcbiAligner.align()

    secho('Aligning OBO Foundry')
    align_obofoundry()

    secho('Aligning OLS')
    align_ols()

    secho('Aligning Wikidata')
    align_wikidata()

    secho('Aligning GO')
    GoAligner.align()

    secho('Aligning BioPortal')
    BioPortalAligner.align()

    secho('Aligning Prefix Commons')
    PrefixCommonsAligner.align()

    secho('Aligning Biolink')
    BiolinkAligner.align()


if __name__ == '__main__':
    align()
