# -*- coding: utf-8 -*-

"""CLI for alignment."""

import click

from ..utils import get_hexdigests, secho

__all__ = [
    "align",
]


@click.command()
@click.option("--skip-fairsharing", is_flag=True)
def align(skip_fairsharing: bool):
    """Align all external registries."""
    from .biocontext import BioContextAligner
    from .biolink import BiolinkAligner
    from .bioportal import BioPortalAligner
    from .cellosaurus import CellosaurusAligner
    from .cheminf import ChemInfAligner
    from .fairsharing import FairsharingAligner
    from .go import GoAligner
    from .miriam import MiriamAligner
    from .n2t import N2TAligner
    from .ncbi import NcbiAligner
    from .obofoundry import OBOFoundryAligner
    from .ols import OLSAligner
    from .ontobee import OntobeeAligner
    from .prefixcommons import PrefixCommonsAligner
    from .uniprot import UniProtAligner
    from .wikidata import WikidataAligner

    pre_digests = get_hexdigests()

    aligner_classes = [
        MiriamAligner,
        N2TAligner,
        NcbiAligner,
        OBOFoundryAligner,
        OLSAligner,
        WikidataAligner,
        GoAligner,
        BioPortalAligner,
        PrefixCommonsAligner,
        BioContextAligner,
        BiolinkAligner,
        UniProtAligner,
        OntobeeAligner,
        CellosaurusAligner,
        ChemInfAligner,
    ]
    if not skip_fairsharing:
        aligner_classes.append(FairsharingAligner)
    for aligner_cls in aligner_classes:
        secho(f"Aligning {aligner_cls.key}")
        try:
            aligner_cls.align()
        except IOError:
            secho(f"Failed to align {aligner_cls.key}", fg="red")

    if pre_digests != get_hexdigests():
        click.echo("::set-output name=BR_UPDATED::true")


if __name__ == "__main__":
    align()
