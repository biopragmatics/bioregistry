# -*- coding: utf-8 -*-

"""Workflows for downloading and aligning various external registries."""

from .miriam import get_miriam, get_miriam_df  # noqa:F401
from .n2t import get_n2t  # noqa:F401
from .obofoundry import get_obofoundry, get_obofoundry_df  # noqa:F401
from .ols import get_ols, get_ols_df  # noqa:F401
from .wikidata import get_wikidata_registry  # noqa:F401
