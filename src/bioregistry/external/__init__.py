# -*- coding: utf-8 -*-

"""Workflows for downloading and aligning various external registries."""

from .biolink import get_biolink  # noqa:F401
from .bioportal import get_bioportal  # noqa:F401
from .go import get_go  # noqa:F401
from .miriam import get_miriam, get_miriam_df  # noqa:F401
from .n2t import get_n2t  # noqa:F401
from .ncbi import get_ncbi  # noqa:F401
from .obofoundry import get_obofoundry, get_obofoundry_df  # noqa:F401
from .ols import get_ols, get_ols_df  # noqa:F401
from .prefix_commons import get_prefix_commons  # noqa:F401
from .uniprot import get_uniprot  # noqa:F401
from .wikidata import get_wikidata_registry  # noqa:F401

GETTERS = [
    ('obofoundry', 'OBO', lambda: get_obofoundry(skip_deprecated=True, mappify=True)),
    ('ols', 'OLS', lambda: get_ols(mappify=True)),
    ('miriam', 'MIRIAM', lambda: get_miriam(skip_deprecated=True, mappify=True)),
    ('wikidata', 'Wikidata', get_wikidata_registry),
    ('n2t', 'N2T', get_n2t),
    ('go', 'GO', lambda: get_go(mappify=True)),
    ('bioportal', 'BioPortal', lambda: get_bioportal(mappify=True)),
    ('prefixcommons', 'Prefix Commons', get_prefix_commons),
    ('biolink', 'Biolink', get_biolink),
    ('ncbi', 'NCBI', get_ncbi),
    ('uniprot', 'UniProt', get_uniprot),
]
