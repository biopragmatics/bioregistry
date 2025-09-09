"""This module is dedicated to parsing the version from an IRI."""

from __future__ import annotations

import re
import typing as t
from urllib.parse import urlparse

from tqdm import tqdm

__all__ = [
    "parse_obo_version_iri",
]

#: Official regex for semantic versions from
#: https://semver.org/#is-there-a-suggested-regular-expression-regex-to-check-a-semver-string
SEMVER_PATTERN = re.compile(
    r"^(0|[1-9]\d*)\.(0|[1-9]\d*)(\.(0|[1-9]\d*))?(?:-((?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)"
    r"(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?(?:\+([0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$"
)
#: Regular expression for ISO 8601 compliant date in YYYY-MM-DD format
DATE_PATTERN = re.compile(r"^([0-9]{4})-(1[0-2]|0[1-9])-(3[01]|0[1-9]|[12][0-9])$")


def _contains_semver(iri: str) -> bool:
    """Return if the IRI contains a semantic version substring."""
    return _match_any_part(iri, SEMVER_PATTERN)


def _contains_date(iri: str) -> bool:
    return _match_any_part(iri, DATE_PATTERN)


def _match_any_part(iri: str, pattern: t.Pattern[str]) -> bool:
    parse_result = urlparse(iri)
    return any(bool(pattern.match(part)) for part in parse_result.path.split("/"))


def parse_obo_version_iri(
    version_iri: str, obo_prefix: str
) -> tuple[str, str | None, str] | tuple[None, None, None]:
    """Parse an OBO version IRI."""
    obo_prefix = obo_prefix.lower()
    parts = [
        ("long", f"http://purl.obolibrary.org/obo/{obo_prefix}/releases/"),
        ("short", f"http://purl.obolibrary.org/obo/{obo_prefix}/"),
    ]
    for version_length, version_iri_prefix in parts:
        if not version_iri.startswith(version_iri_prefix):
            continue
        try:
            version, filename = version_iri[len(version_iri_prefix) :].split("/", 1)
        except ValueError:
            tqdm.write(f"[{obo_prefix}] issue parsing IRI back-half: {version_iri}")
            return None, None, None
        if not any(
            filename.startswith(f"{obo_prefix}.{ext}") for ext in ("json", "owl", "obo", "ofn")
        ):
            return None, None, None
        version_type: str | None
        if SEMVER_PATTERN.fullmatch(version):
            version_type = "semver"
        elif DATE_PATTERN.fullmatch(version):
            version_type = "date"
        else:
            version_type = None
        # remove leading v, we know it's a version
        version = version.lstrip("v")
        return version_length, version_type, version
    return None, None, None
