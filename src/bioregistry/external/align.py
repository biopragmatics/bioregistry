# -*- coding: utf-8 -*-

"""Workflows for aligning external registries."""

from class_resolver import ClassResolver

from .aberowl import AberOWLAligner
from .alignment_utils import Aligner
from .bartoc import BartocAligner
from .biocontext import BioContextAligner
from .biolink import BiolinkAligner
from .bioportal.bioportal import (
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
from .hl7 import HL7Aligner
from .integbio import IntegbioAligner
from .lov import LOVAligner
from .miriam import MiriamAligner
from .n2t import N2TAligner
from .ncbi import NcbiAligner
from .obofoundry import OBOFoundryAligner
from .ols import OLSAligner
from .ontobee import OntobeeAligner
from .pathguide import PathguideAligner
from .prefixcommons import PrefixCommonsAligner
from .re3data import Re3dataAligner
from .rrid import RRIDAligner
from .togoid import TogoIDAligner
from .uniprot import UniProtAligner
from .wikidata import WikidataAligner
from .zazuko import ZazukoAligner

__all__ = [
    # Abstract
    "Aligner",
    "aligner_resolver",
    # Concrete
    "AberOWLAligner",
    "BartocAligner",
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
    "HL7Aligner",
    "ZazukoAligner",
    "LOVAligner",
    "IntegbioAligner",
    "PathguideAligner",
    "RRIDAligner",
    "TogoIDAligner",
]

aligner_resolver = ClassResolver.from_subclasses(
    base=Aligner,
    skip={OntoPortalAligner},
)
