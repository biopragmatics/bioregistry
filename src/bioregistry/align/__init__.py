# -*- coding: utf-8 -*-

"""Workflows for aligning external registries."""


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
from .utils import Aligner
from .wikidata import WikidataAligner

__all__ = [
    # Abstract
    "Aligner",
    "ALIGNERS",
    # Concrete
    "BioContextAligner",
    "BiolinkAligner",
    "BioPortalAligner",
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
]

ALIGNERS = [sc for sc in Aligner.__subclasses__() if hasattr(sc, "key")]
