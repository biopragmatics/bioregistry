# -*- coding: utf-8 -*-

"""Data in the bioregistry."""

import enum
import json
import pathlib
from functools import lru_cache
from typing import Mapping, Optional

from pydantic import BaseModel

HERE = pathlib.Path(__file__).parent.resolve()

EXTERNAL = HERE / "external"
OLS_PROCESSING = HERE / "processing_ols.json"


class VersionType(str, enum.Enum):
    """Types for OLS ontology versions."""

    date = "date"
    semver = "semver"
    other = "other"
    sequential = "sequential"
    garbage = "garbage"
    missing = "missing"


class OLSConfig(BaseModel):
    """Configuration for processing an OLS ontology."""

    prefix: str
    version_type: VersionType
    version_date_format: Optional[str]
    version_prefix: Optional[str]
    version_suffix: Optional[str]
    version_suffix_split: Optional[str]
    version_iri_prefix: Optional[str]
    version_iri_suffix: Optional[str]


@lru_cache(maxsize=1)
def get_ols_processing() -> Mapping[str, OLSConfig]:
    """Get OLS processing configurations."""
    with OLS_PROCESSING.open() as file:
        data = json.load(file)
    return {record["prefix"]: OLSConfig(**record) for record in data["configurations"]}
