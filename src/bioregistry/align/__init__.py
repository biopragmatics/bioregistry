# -*- coding: utf-8 -*-

"""Workflows for aligning external registries."""

from class_resolver import ClassResolver

from .aberowl import AberOWLAligner
from .biocontext import BioContextAligner
from .biolink import BiolinkAligner
from .bioportal import (
    AgroPortalAligner,
    BioPortalAligner,
    EcoPortalAligner,
    OntoPortalAligner,
)
from .cellosaurus import CellosaurusAligner
from .cheminf import ChemInfAligner
from .cropoct import CropOCTAligner
from .edam import EDAMAligner
from .fairsharing import FairsharingAligner
from .go import GoAligner
from .miriam import MiriamAligner
from .n2t import N2TAligner
from .ncbi import NcbiAligner
from .obofoundry import OBOFoundryAligner
from .ols import OLSAligner
from .ontobee import OntobeeAligner
from .prefixcommons import PrefixCommonsAligner
from .re3data import Re3dataAligner
from .uniprot import UniProtAligner
from .utils import Aligner
from .wikidata import WikidataAligner

__all__ = [
    # Abstract
    "Aligner",
    "aligner_resolver",
    # Concrete
    "AberOWLAligner",
    "BioContextAligner",
    "BiolinkAligner",
    "BioPortalAligner",
    "CropOCTAligner",
    "EcoPortalAligner",
    "AgroPortalAligner",
    "CellosaurusAligner",
    "ChemInfAligner",
    "FairsharingAligner",
    "GoAligner",
    "MiriamAligner",
    "N2TAligner",
    "NcbiAligner",
    "OBOFoundryAligner",
    "OLSAligner",
    "OntobeeAligner",
    "PrefixCommonsAligner",
    "UniProtAligner",
    "WikidataAligner",
    "EDAMAligner",
    "Re3dataAligner",
]

aligner_resolver = ClassResolver.from_subclasses(
    base=Aligner,
    skip={OntoPortalAligner},
)
