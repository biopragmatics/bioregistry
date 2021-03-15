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
from .wikidata import get_wikidata_registry  # noqa:F401
