"""Download registry information from the OLS."""

import datetime
import enum
import json
import logging
from collections.abc import Mapping
from email.utils import parseaddr
from functools import lru_cache
from operator import itemgetter
from pathlib import Path
from textwrap import dedent
from typing import Any, Optional

import requests
from pydantic import BaseModel

from bioregistry.constants import RAW_DIRECTORY
from bioregistry.external.alignment_utils import Aligner
from bioregistry.parse_version_iri import parse_obo_version_iri
from bioregistry.utils import OLSBroken

__all__ = [
    "OLSAligner",
    "get_ols",
]

logger = logging.getLogger(__name__)

DIRECTORY = Path(__file__).parent.resolve()
URL = "https://www.ebi.ac.uk/ols4/api/ontologies?size=1000"
RAW_PATH = RAW_DIRECTORY / "ols.json"
PROCESSED_PATH = DIRECTORY / "processed.json"
OLS_PROCESSING = DIRECTORY / "processing_ols.json"

OLS_SKIP = {
    "co_321:root": "this is a mistake in the way OLS imports CO",
    "phi": "this is low quality and has no associated metadata",
    "epso": "can't figure out / not sure if still exists",
    "epio": "can't figure out / not sure if still exists",
    "cpont": "no own terms?",
    "schemaorg_https": "duplicate of canonical HTTP version",
    "hpi": "nonsensical duplication of HP",
}


def get_ols(force_download: bool = False):
    """Get the OLS registry."""
    if PROCESSED_PATH.exists() and not force_download:
        with PROCESSED_PATH.open() as file:
            return json.load(file)

    data = requests.get(URL).json()
    if "_embedded" not in data:
        raise OLSBroken
    data["_embedded"]["ontologies"] = sorted(
        data["_embedded"]["ontologies"],
        key=itemgetter("ontologyId"),
    )
    if "next" in data["_links"]:
        raise NotImplementedError(
            "Need to implement paging since there are more entries than fit into one page"
        )
    RAW_PATH.write_text(json.dumps(data, indent=2, sort_keys=True))

    processed = {}
    for ontology in data["_embedded"]["ontologies"]:
        ols_id = ontology["ontologyId"]
        if ols_id in OLS_SKIP:
            continue
        # TODO better docs on how to maintain this file
        config = get_ols_processing().get(ols_id)
        if config is None:
            if ols_id not in OLS_SKIP:
                logger.warning("[%s] need to curate processing file", ols_id)
            continue
        processed[ols_id] = _process(ontology, config)

    with PROCESSED_PATH.open("w") as file:
        json.dump(processed, file, indent=2, sort_keys=True)
    return processed


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
    version_date_format: Optional[str] = None
    version_prefix: Optional[str] = None
    version_suffix: Optional[str] = None
    version_suffix_split: Optional[str] = None
    version_iri_prefix: Optional[str] = None
    version_iri_suffix: Optional[str] = None


def _get_email(ols_id, config) -> Optional[str]:
    mailing_list = config.get("mailingList")
    if not mailing_list:
        return None
    name, email = parseaddr(mailing_list)
    if email.startswith("//"):
        logger.debug("[%s] invalid email address: %s", ols_id, mailing_list)
        return None
    return email


def _get_license(ols_id, config) -> Optional[str]:
    license_value = (config.get("annotations") or {}).get("license", [None])[0]
    if license_value == "Unspecified":
        logger.info("[%s] unspecified license in OLS. Contact: %s", ols_id, config["mailingList"])
        return None
    if not license_value:
        logger.info("[%s] missing license in OLS. Contact: %s", ols_id, config["mailingList"])
    return license_value


def _get_version(ols_id, config, processing: OLSConfig) -> Optional[str]:
    version_iri = config.get("versionIri")
    if version_iri:
        _, _, version = parse_obo_version_iri(version_iri, ols_id)
        if version:
            return version

    version = config.get("version")
    if version is None and processing.version_iri_prefix:
        if not version_iri.startswith(processing.version_iri_prefix):
            logger.info("[%s] version IRI does not start with appropriate prefix", ols_id)
        else:
            version = version_iri[len(processing.version_iri_prefix) :]
            if processing.version_iri_suffix:
                version = version[: -len(processing.version_iri_suffix)]

    if version is None:
        logger.info(
            "[%s] missing version in OLS. Contact: %s, consider version.iri %s",
            ols_id,
            config["mailingList"],
            version_iri,
        )
    else:
        if version != version.strip():
            logger.info(
                "[%s] extra whitespace in version: %s. Contact: %s",
                ols_id,
                version,
                config["mailingList"],
            )
            version = version.strip()

        version_prefix = processing.version_prefix
        if version_prefix:
            if not version.startswith(version_prefix):
                raise ValueError(
                    dedent(
                        f"""\
                    [{ols_id}] version "{version}" does not start with prefix "{version_prefix}".
                    Update the ["{ols_id}"]["prefix"] entry in the OLS processing configuration.
                    """
                    )
                )
            version = version[len(version_prefix) :]
        if processing.version_suffix_split:
            version = version.split()[0]
        version_suffix = processing.version_suffix
        if version_suffix:
            if not version.endswith(version_suffix):
                raise ValueError(
                    f"[{ols_id}] version {version} does not end with prefix {version_suffix}"
                )
            version = version[: -len(version_suffix)]

        version_type = processing.version_type
        version_date_fmt = processing.version_date_format
        if version_date_fmt:
            if version_date_fmt in {"%Y-%d-%m"}:
                logger.info(
                    "[%s] confusing date format: %s. Contact: %s",
                    ols_id,
                    version_date_fmt,
                    config["mailingList"],
                )
            try:
                version = datetime.datetime.strptime(version, version_date_fmt).strftime("%Y-%m-%d")
            except ValueError:
                logger.info("[%s] wrong format for version %s", ols_id, version)
        elif not version_type:
            logger.info("[%s] no type for version %s", ols_id, version)

    return version


def _process(ols_entry: Mapping[str, Any], processing: OLSConfig) -> Optional[Mapping[str, str]]:
    ols_id = ols_entry["ontologyId"]
    config = ols_entry["config"]
    version_iri = config["versionIri"]
    title = config.get("title") or config.get("localizedTitles", {}).get("en")
    description = config.get("description") or config.get("localizedDescriptions", {}).get("en")
    rv = {
        "prefix": ols_id,
        # "preferred_prefix": config["preferredPrefix"],
        "name": title,
        "version.iri": _clean_url(version_iri),
        "version": _get_version(ols_id, config, processing),
        "description": description,
        "homepage": _clean_url(config["homepage"]),
        # "tracker": _clean_url(config["tracker"]),
        "contact": _get_email(ols_id, config),
        "license": _get_license(ols_id, config),
    }
    download = _clean_url(config["fileLocation"])
    if download is None:
        pass
    elif download.endswith(".obo"):
        rv["download_obo"] = download
    elif download.endswith(".owl"):
        rv["download_owl"] = download
    elif download.endswith(".rdf") or download.endswith(".ttl"):
        rv["download_rdf"] = download
    else:
        logger.warning("[%s] unknown download type %s", ols_id, download)
    rv = {k: v.strip() for k, v in rv.items() if v}
    return rv


def _clean_url(url: Optional[str]) -> Optional[str]:
    if url is None:
        return url
    if "CO_" in url and url.startswith("http://127.0.0.1:5900"):
        return "https://cropontology.org" + url[len("http://127.0.0.1:5900") :]
    return url


@lru_cache(maxsize=1)
def get_ols_processing() -> Mapping[str, OLSConfig]:
    """Get OLS processing configurations."""
    with OLS_PROCESSING.open() as file:
        data = json.load(file)
    return {record["prefix"]: OLSConfig(**record) for record in data["configurations"]}


class OLSAligner(Aligner):
    """Aligner for the OLS."""

    key = "ols"
    getter = get_ols
    curation_header = ("name",)
    include_new = True

    def get_skip(self) -> Mapping[str, str]:
        """Get skipped entries from OLS."""
        return OLS_SKIP


if __name__ == "__main__":
    OLSAligner.cli()
