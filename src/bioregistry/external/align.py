# -*- coding: utf-8 -*-

"""Workflows for aligning external registries."""

from class_resolver import ClassResolver

from .aberowl import AberOWLAligner
from .alignment_utils import Aligner
from .bartoc import BartocAligner
from .biocontext.biocontext import BioContextAligner
from .biolink.biolink import BiolinkAligner
from .bioportal.bioportal import (
    AgroPortalAligner,
    BioPortalAligner,
    EcoPortalAligner,
    OntoPortalAligner,
)
from .cellosaurus.cellosaurus import CellosaurusAligner
from .cheminf.cheminf import ChemInfAligner
from .cropoct.cropoct import CropOCTAligner
from .edam.edam import EDAMAligner
from .fairsharing.fairsharing import FairsharingAligner
from .go.go import GoAligner
from .hl7.hl7 import HL7Aligner
from .integbio.integbio import IntegbioAligner
from .lov.lov import LOVAligner
from .miriam.miriam import MiriamAligner
from .n2t.n2t import N2TAligner
from .ncbi.ncbi import NcbiAligner
from .obofoundry.obofoundry import OBOFoundryAligner
from .ols.ols import OLSAligner
from .ontobee.ontobee import OntobeeAligner
from .pathguide.pathguide import PathguideAligner
from .prefixcommons.prefixcommons import PrefixCommonsAligner
from .re3data.re3data import Re3dataAligner
from .scicrunch.rrid import RRIDAligner
from .togoid.togoid import TogoIDAligner
from .uniprot.uniprot import UniProtAligner
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
