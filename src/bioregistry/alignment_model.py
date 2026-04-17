"""Data models for standard external registry import."""

from __future__ import annotations

import datetime
import enum
import json
from pathlib import Path
from typing import Annotated, Any

from curies import NamableReference
from pydantic import BaseModel, EmailStr, Field

from .constants import ORCID_FIELD, ROR_FIELD


class Person(BaseModel):
    """Represents the fields for a person."""

    name: str | None = None
    orcid: Annotated[str | None, ORCID_FIELD] = None
    email: EmailStr | None = None
    github: str | None = None


class Organization(BaseModel):
    """Represents a organization."""

    name: str
    ror: Annotated[str, ROR_FIELD]


class License(BaseModel):
    """Represents the fields for a license."""

    name: str | None = None
    spdx: str | None = None
    url: str | None = None


class Status(str, enum.Enum):
    """Represents the project status."""

    active = "active"
    inactive = "inactive"
    abandoned = "abandoned"
    orphaned = "orphaned"
    replaced = "replaced"
    deprecated = "deprecated"


class Publication(BaseModel):
    """Represents a publication."""

    title: str | None = None
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


class ArtifactType(str, enum.Enum):
    """A semantic space artifact type."""

    obo = "obo"
    obograph_json = "obograph_json"
    rdf = "rdf"
    owl = "owl"
    xml = "xml"


class Artifact(BaseModel):
    """Represents an artifact and its type."""

    url: str
    type: ArtifactType
    description: str | None = None


class Provider(BaseModel):
    """Represents a provider."""

    code: str
    uri_format: str
    homepage: str | None = None
    description: str | None = None
    name: str | None = None


class Record(BaseModel):
    """Represents a record in a semantic space registry."""

    preferred_prefix: str | None = None
    name: str | None = None
    version: str | None = None
    description: str | None = None
    status: Status | None = None
    homepage: str | None = None
    repository: str | None = None
    tracker: str | None = None
    license: License | None = None
    contact: Person | None = None
    domain: str | None = None
    logo: str | None = Field(None, description="URL for the logo")
    depends_on: list[str] | None = None
    appears_in: list[str] | None = None
    publications: list[Publication] | None = None
    artifacts: list[Artifact] | None = None
    taxon: NamableReference | None = None
    short_names: list[str] | None = Field(
        None,
        description="A short name/abbreviation for records where the primary key is not the prefix, such as wikidata.",
    )
    uri_format: str | None = None
    uri_format_rdf: str | None = None
    pattern: str | None = None
    examples: list[str] | None = None
    keywords: list[str] | None = None
    modified: datetime.datetime | None = Field(None, description="Date last modified")
    xrefs: dict[str, str] | None = None
    prefix_synonyms: list[str] | None = None
    providers: list[Provider] | None = None
    owners: list[Organization] | None = None
    extras: dict[str, Any] | None = Field(None, description="Extras specific to the resource.")


def make_record(record: dict[str, Any]) -> Record:
    """Make a record."""
    # TODO what about stripping strings in lists?
    #     rv = {k: v.strip() if isinstance(v, str) else v for k, v in data.items() if v}
    record = {k: v for k, v in record.items() if k and v and k != "prefix"}
    return Record.model_validate(record, extra="forbid")


class Registry(BaseModel):
    """Represents a semantic space registry."""

    records: dict[str, Record] = Field(default_factory=dict)
    metadata: dict[str, str] = Field(default_factory=dict)


def dump_records(records: dict[str, Record], path: Path) -> None:
    """Dump records."""
    rv = {
        k: r.model_dump(exclude_unset=True, exclude_none=True, exclude_defaults=True)
        for k, r in records.items()
    }
    with path.open("w") as file:
        json.dump(rv, file, indent=2, sort_keys=True, ensure_ascii=False)


def load_processed(path: Path) -> dict[str, Record]:
    """Load records."""
    with path.open() as file:
        rv = json.load(file)
    return {k: Record.model_validate(v) for k, v in rv.items()}
