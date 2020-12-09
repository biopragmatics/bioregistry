# -*- coding: utf-8 -*-

"""Workflows for downloading and aligning various external registries."""

from .miriam import get_miriam_df, get_miriam_registry  # noqa:F401
from .obofoundry import get_obofoundry, get_obofoundry_df  # noqa:F401
from .ols import get_ols, get_ols_df  # noqa:F401
