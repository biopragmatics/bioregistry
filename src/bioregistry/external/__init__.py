# -*- coding: utf-8 -*-

"""Workflows for downloading and aligning various external registries."""

from typing import Callable, List, Tuple

from .aberowl import get_aberowl
from .biocontext import get_biocontext
from .biolink import get_biolink
from .bioportal import get_agroportal, get_bioportal, get_ecoportal
from .cellosaurus import get_cellosaurus
from .cheminf import get_cheminf
from .cropoct import get_cropoct
from .edam import get_edam
from .fairsharing import get_fairsharing
from .go import get_go
from .miriam import get_miriam
from .n2t import get_n2t
from .ncbi import get_ncbi
from .obofoundry import get_obofoundry
from .ols import get_ols
from .ontobee import get_ontobee
from .prefixcommons import get_prefixcommons
from .re3data import get_re3data
from .uniprot import get_uniprot
from .wikidata import get_wikidata

__all__ = [
    "GETTERS",
    # Getter functions
    "get_biocontext",
    "get_biolink",
    "get_bioportal",
    "get_cellosaurus",
    "get_cheminf",
    "get_fairsharing",
    "get_go",
    "get_miriam",
    "get_n2t",
    "get_ncbi",
    "get_obofoundry",
    "get_ols",
    "get_ontobee",
    "get_prefixcommons",
    "get_uniprot",
    "get_wikidata",
    "get_edam",
    "get_re3data",
]

GETTERS: List[Tuple[str, str, Callable]] = [
    ("obofoundry", "OBO", get_obofoundry),
    ("ols", "OLS", get_ols),
    ("miriam", "MIRIAM", get_miriam),
    ("wikidata", "Wikidata", get_wikidata),
    ("n2t", "N2T", get_n2t),
    ("go", "GO", get_go),
    ("bioportal", "BioPortal", get_bioportal),
    ("prefixcommons", "Prefix Commons", get_prefixcommons),
    ("biocontext", "BioContext", get_biocontext),
    ("biolink", "Biolink", get_biolink),
    ("ncbi", "NCBI", get_ncbi),
    ("uniprot", "UniProt", get_uniprot),
    ("cellosaurus", "Cellosaurus", get_cellosaurus),
    ("ontobee", "OntoBee", get_ontobee),
    ("cheminf", "CHEMINF", get_cheminf),
    ("fairsharing", "FAIRsharing", get_fairsharing),
    ("agroportal", "AgroPortal", get_agroportal),
    ("ecoportal", "EcoPortal", get_ecoportal),
    ("aberowl", "AberOWL", get_aberowl),
    ("cropoct", "CropOCT", get_cropoct),
    ("edam", "EDAM", get_edam),
    ("re3data", "re3data", get_re3data),
]
