# -*- coding: utf-8 -*-

"""CLI for alignment."""

import click
from pystow.utils import get_hashes

from ..utils import BIOREGISTRY_PATH, secho

__all__ = [
    "align",
]


def _get_hexdigest(alg: str = "sha256") -> str:
    hashes = get_hashes(BIOREGISTRY_PATH, [alg])
    return hashes[alg].hexdigest()


@click.command()
def align():
    """Align all external registries."""
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
    from .prefix_commons import PrefixCommonsAligner
    from .uniprot import UniProtAligner
    from .wikidata import WikidataAligner

    pre_sha256 = _get_hexdigest()

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
        OntobeeAligner,
        CellosaurusAligner,
        ChemInfAligner,
        FairsharingAligner,
    ]:
        secho(f"Aligning {aligner_cls.key}")
        try:
            aligner_cls.align()
        except IOError:
            secho(f"Failed to align {aligner_cls.key}", fg="red")

    if pre_sha256 != _get_hexdigest():
        click.echo("::set-output name=BR_UPDATED::true")


if __name__ == "__main__":
    align()
