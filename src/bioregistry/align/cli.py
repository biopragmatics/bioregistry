# -*- coding: utf-8 -*-

"""CLI for alignment."""

import click

from .miriam import align_miriam
from .n2t import align_n2t
from .obofoundry import align_obofoundry
from .ols import align_ols
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

    secho('Aligning OBO Foundry')
    align_obofoundry()

    secho('Aligning OLS')
    align_ols()

    secho('Aligning Wikidata')
    align_wikidata()


if __name__ == '__main__':
    align()
