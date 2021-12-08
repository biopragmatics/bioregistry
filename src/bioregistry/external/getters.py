# -*- coding: utf-8 -*-

"""List of getters."""

from typing import Callable, List, Tuple

from .biolink import get_biolink  # noqa:F401
from .bioportal import get_bioportal  # noqa:F401
from .cellosaurus import get_cellosaurus  # noqa:F401
from .cheminf import get_cheminf  # noqa:F401
from .go import get_go  # noqa:F401
from .miriam import get_miriam  # noqa:F401
from .n2t import get_n2t  # noqa:F401
from .ncbi import get_ncbi  # noqa:F401
from .obofoundry import get_obofoundry  # noqa:F401
from .ols import get_ols  # noqa:F401
from .ontobee import get_ontobee  # noqa:F401
from .prefix_commons import get_prefix_commons  # noqa:F401
from .uniprot import get_uniprot  # noqa:F401
from .wikidata import get_wikidata  # noqa:F401

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
    ("cheminf", "Chemical Information Ontology", get_cheminf),
]
