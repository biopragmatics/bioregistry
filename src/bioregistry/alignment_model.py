"""Data models for standard external registry import."""

from __future__ import annotations

import enum
import json
from pathlib import Path

from curies import NamableReference
from pydantic import BaseModel, Field


class Person(BaseModel):
    name: str | None = None
    orcid: str | None = None
    email: str | None = None
    github: str | None = None


class License(BaseModel):
    name: str | None = None
    spdx: str | None = None
    url: str | None = None


class Status(enum.StrEnum):
    active = enum.auto()
    inactive = enum.auto()
    abandoned = enum.auto()
    orphaned = enum.auto()
    replaced = enum.auto()
    deprecated = enum.auto()


class Publication(BaseModel):
    name: str | None = None
    year: int | None = None
    url: str | None = None

    # IDs
    doi: str | None = None
    pubmed: str | None = None
    pmc: str | None = None
    arxiv: str | None = None
    medrxiv: str | None = None
    biorxiv: str | None = None
    zenodo: str | None = None


class ArtifactType(enum.StrEnum):
    obo = enum.auto()
    obograph_json = enum.auto()
    rdf = enum.auto()
    owl = enum.auto()


class Artifact(BaseModel):
    url: str
    type: ArtifactType
    description: str | None = None


class Record(BaseModel):
    # prefix: str
    preferred_prefix: str | None = None
    name: str | None = None
    description: str | None = None
    status: Status | None = None
    homepage: str | None = None
    repository: str | None = None
    license: License | None = None
    contact: Person | None = None
    domain: str | None = None
    logo: str | None = Field(None, description="URL for the logo")
    depends_on: list[str] = Field(default_factory=list)
    appears_in: list[str] = Field(default_factory=list)
    publications: list[Publication] = Field(default_factory=list)
    artifacts: list[Artifact] = Field(default_factory=list)
    taxon: NamableReference | None = None
    uri_format: str | None = None


class Registry(BaseModel):
    records: dict[str, Record]
    metadata: dict[str, str] = Field(default_factory=dict)


def dump_records(records: dict[str, Record], path: Path) -> None:
    """Dump records."""
    rv = {
        k: r.model_dump(exclude_unset=True, exclude_none=True, exclude_defaults=True)
        for k, r in records.items()
    }
    with path.open("w") as file:
        json.dump(rv, file, indent=2, sort_keys=True)


def load_records(path: Path) -> dict[str, Record]:
    """Load records."""
    with path.open() as file:
        rv = json.load(file)
    return {k: Record.model_validate(v) for k, v in rv.items()}
