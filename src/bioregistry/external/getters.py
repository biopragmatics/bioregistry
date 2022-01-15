# -*- coding: utf-8 -*-

"""List of getters."""

from typing import Callable, List, Tuple

from .biolink import get_biolink
from .bioportal import get_bioportal
from .cellosaurus import get_cellosaurus
from .cheminf import get_cheminf
from .fairsharing import get_fairsharing
from .go import get_go
from .miriam import get_miriam
from .n2t import get_n2t
from .ncbi import get_ncbi
from .obofoundry import get_obofoundry
from .ols import get_ols
from .ontobee import get_ontobee
from .prefix_commons import get_prefix_commons
from .uniprot import get_uniprot
from .wikidata import get_wikidata

__all__ = [
    "GETTERS",
]

GETTERS: List[Tuple[str, str, Callable]] = [
    ("obofoundry", "OBO", get_obofoundry),
    ("ols", "OLS", get_ols),
    ("miriam", "MIRIAM", get_miriam),
    ("wikidata", "Wikidata", get_wikidata),
    ("n2t", "N2T", get_n2t),
    ("go", "GO", get_go),
    ("bioportal", "BioPortal", get_bioportal),
    ("prefixcommons", "Prefix Commons", get_prefix_commons),
    ("biolink", "Biolink", get_biolink),
    ("ncbi", "NCBI", get_ncbi),
    ("uniprot", "UniProt", get_uniprot),
    ("cellosaurus", "Cellosaurus", get_cellosaurus),
    ("ontobee", "OntoBee", get_ontobee),
    ("cheminf", "CHEMINF", get_cheminf),
    ("fairsharing", "FAIRsharing", get_fairsharing),
]
