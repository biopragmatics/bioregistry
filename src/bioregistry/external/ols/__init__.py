"""Download registry information from the OLS."""

from __future__ import annotations

import datetime
import enum
import json
import logging
from collections.abc import Mapping, Sequence
from email.utils import parseaddr
from operator import itemgetter
from pathlib import Path
from textwrap import dedent
from typing import Any, ClassVar

import requests
from pydantic import BaseModel

from bioregistry.alignment_model import (
    Artifact,
    ArtifactType,
    License,
    Person,
    Record,
    dump_records,
    load_processed,
    make_record,
)
from bioregistry.constants import RAW_DIRECTORY, URI_FORMAT_KEY
from bioregistry.external.alignment_utils import Aligner, adapter
from bioregistry.parse_version_iri import parse_obo_version_iri
from bioregistry.utils import OLSBrokenError

__all__ = [
    "OLSAligner",
    "get_ols",
    "get_ols_base",
    "get_ols_processing",
]

logger = logging.getLogger(__name__)


DIRECTORY = Path(__file__).parent.resolve()
RAW_PATH = RAW_DIRECTORY / "ols.json"
PROCESSED_PATH = DIRECTORY / "processed.json"
EBI_OLS_VERSION_PROCESSING_CONFIG_PATH = DIRECTORY / "processing_ols.json"

EBI_OLS_SKIP = {
    "co_321:root": "this is a mistake in the way OLS imports CO",
    "phi": "this is low quality and has no associated metadata",
    "epso": "can't figure out / not sure if still exists",
    "epio": "can't figure out / not sure if still exists",
    "cpont": "no own terms?",
    "schemaorg_https": "duplicate of canonical HTTP version",
    "hpi": "nonsensical duplication of HP",
    "hra": "project ontology",
}

EBI_OLS_BASE_URL = "https://www.ebi.ac.uk/ols4/api"


@adapter
def get_ols(*, force_download: bool = False, force_process: bool = False) -> dict[str, Record]:
    """Get the EBI OLS registry."""
    return get_ols_base(
        force_download=force_download,
        force_process=force_process,
        base_url=EBI_OLS_BASE_URL,
        processed_path=PROCESSED_PATH,
        raw_path=RAW_PATH,
        version_processing_config_path=EBI_OLS_VERSION_PROCESSING_CONFIG_PATH,
    )


def get_ols_base(
    *,
    force_download: bool = False,
    force_process: bool = False,
    base_url: str,
    processed_path: Path,
    raw_path: Path,
    version_processing_config_path: Path | None = None,
    skip_uri_format: set[str] | None = None,
) -> dict[str, Record]:
    """Get an OLS registry."""
    if processed_path.exists() and not force_download and not force_process:
        return load_processed(processed_path)

    _download(base_url, raw_path=raw_path, force=force_download)

    version_processing_configurations = (
        _load_version_processing_configurations(version_processing_config_path)
        if version_processing_config_path is not None and version_processing_config_path.is_file()
        else {}
    )
    processed = {}
    with raw_path.open() as file:
        data = json.load(file)
        for ontology in data["_embedded"]["ontologies"]:
            ols_id = ontology["ontologyId"]
            if ols_id in EBI_OLS_SKIP:
                continue
            # TODO better docs on how to maintain this file
            version_processing_config = version_processing_configurations.get(ols_id)
            if version_processing_config is None:
                logger.debug("[%s] need to curate processing file", ols_id)
            record = _process(
                ontology,
                version_processing_config=version_processing_config,
                skip_uri_format=skip_uri_format,
            )
            if not record:
                continue
            processed[ols_id] = record

    dump_records(processed, processed_path)
    return processed


def _download(base_url: str, raw_path: Path, force: bool = False) -> None:
    if raw_path.is_file() and not force:
        return
    data = requests.get(f"{base_url}/ontologies", timeout=15, params={"size": 1000}).json()
    if "_embedded" not in data:
        raise OLSBrokenError(f"data did not contain an `_embedded` key. Got keys: {set(data)}")
    data["_embedded"]["ontologies"] = sorted(
        data["_embedded"]["ontologies"],
        key=itemgetter("ontologyId"),
    )
    if "next" in data["_links"]:
        raise NotImplementedError(
            "Need to implement paging since there are more entries than fit into one page"
        )
    raw_path.write_text(json.dumps(data, indent=2, sort_keys=True, ensure_ascii=False))


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
    version_date_format: str | None = None
    version_prefix: str | None = None
    version_suffix: str | None = None
    version_suffix_split: str | None = None
    version_iri_prefix: str | None = None
    version_iri_suffix: str | None = None


def _get_contact(ols_id: str, config: dict[str, Any]) -> Person | None:
    mailing_list = config.get("mailingList")
    if not mailing_list:
        return None
    name, email = parseaddr(mailing_list)
    if email.startswith("//"):
        logger.debug("[%s] invalid email address: %s", ols_id, mailing_list)
        return None
    return Person(email=email, name=name or None)


def _get_license(ols_id: str, config: dict[str, Any]) -> License | None:
    license_value: str | None = (config.get("annotations") or {}).get("license", [None])[0]
    if license_value == "Unspecified":
        logger.info("[%s] unspecified license in OLS. Contact: %s", ols_id, config["mailingList"])
        return None
    if not license_value:
        logger.info("[%s] missing license in OLS. Contact: %s", ols_id, config["mailingList"])
        return None
    return License(name=license_value)


def _get_version(
    ols_id: str, config: dict[str, Any], *, version_processing_config: OLSConfig | None = None
) -> str | None:
    if version_processing_config is None:
        return None

    version_iri: str | None = config.get("versionIri")
    if version_iri:
        _, _, version_from_iri = parse_obo_version_iri(version_iri, ols_id)
        if version_from_iri:
            return version_from_iri

    version: str | None = config.get("version")
    if version is None and version_iri and version_processing_config.version_iri_prefix:
        if not version_iri.startswith(version_processing_config.version_iri_prefix):
            logger.info("[%s] version IRI does not start with appropriate prefix", ols_id)
        else:
            version_cut = version_iri[len(version_processing_config.version_iri_prefix) :]
            if version_processing_config.version_iri_suffix:
                version_cut = version_cut[: -len(version_processing_config.version_iri_suffix)]
            return version_cut

    if version is None:
        logger.info(
            "[%s] missing version in OLS. Contact: %s, consider version.iri %s",
            ols_id,
            config["mailingList"],
            version_iri,
        )
        return None

    if version != version.strip():
        logger.info(
            "[%s] extra whitespace in version: %s. Contact: %s",
            ols_id,
            version,
            config["mailingList"],
        )
        version = version.strip()

    version_prefix = version_processing_config.version_prefix
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
    if version_processing_config.version_suffix_split:
        version = version.split()[0]
    version_suffix = version_processing_config.version_suffix
    if version_suffix:
        if not version.endswith(version_suffix):
            raise ValueError(
                f"[{ols_id}] version {version} does not end with prefix {version_suffix}"
            )
        version = version[: -len(version_suffix)]

    version_type = version_processing_config.version_type
    version_date_fmt = version_processing_config.version_date_format
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


def _process(
    ols_entry: Mapping[str, Any],
    *,
    version_processing_config: OLSConfig | None = None,
    skip_uri_format: set[str] | None = None,
) -> Record:
    ols_id = ols_entry["ontologyId"]
    config = ols_entry["config"]
    version_iri = config["versionIri"]
    title = config.get("title") or config.get("localizedTitles", {}).get("en")
    description = config.get("description") or config.get("localizedDescriptions", {}).get("en")

    keywords = []
    for x in config.get("classifications", []):
        keywords.extend(x.get("collection", []))
        keywords.extend(y for s in x.get("subject", []) if (y := s.lower()) != "general")

    rv = {
        "prefix": ols_id,
        # "preferred_prefix": config["preferredPrefix"],
        "name": title,
        "version": _get_version(
            ols_id, config, version_processing_config=version_processing_config
        ),
        "description": description,
        "homepage": _clean_url(config["homepage"]),
        "tracker": _clean_url(config["tracker"]),
        "contact": _get_contact(ols_id, config),
        "license": _get_license(ols_id, config),
        "keywords": keywords,
    }

    if clean_version_iri := _clean_url(version_iri):
        rv.setdefault("extras", {})["version.iri"] = clean_version_iri

    # TODO automatically extract github/gitlab repository based
    #  on tracker / homepage

    base_uris = config.get("baseUris", [])
    if base_uris and (not skip_uri_format or ols_id not in skip_uri_format):
        rv[URI_FORMAT_KEY] = base_uris[0] + "$1"

    download = _clean_url(config["fileLocation"])
    if download is None:
        pass
    elif download.endswith(".obo") or download.endswith(".obo.gz"):
        rv.setdefault("artifacts", []).append(Artifact(type=ArtifactType.obo, url=download))
    elif download.endswith(".owl") or download.endswith(".owl.gz"):
        rv.setdefault("artifacts", []).append(Artifact(type=ArtifactType.owl, url=download))
    elif download.endswith(".rdf") or download.endswith(".ttl") or download.endswith(".ttl.gz"):
        rv.setdefault("artifacts", []).append(Artifact(type=ArtifactType.rdf, url=download))
    elif download.endswith(".xml"):
        rv.setdefault("artifacts", []).append(Artifact(type=ArtifactType.xml, url=download))
    else:
        logger.debug("[%s] unknown download type %s", ols_id, download)
    return make_record(rv)


def _clean_url(url: str | None) -> str | None:
    if url is None:
        return None
    url = url.strip()
    if "CO_" in url and url.startswith("http://127.0.0.1:5900"):
        return "https://cropontology.org" + url[len("http://127.0.0.1:5900") :]
    if url.startswith("file:"):
        return None
    return url


def get_ols_processing() -> Mapping[str, OLSConfig]:
    """Get OLS processing configurations."""
    return _load_version_processing_configurations(EBI_OLS_VERSION_PROCESSING_CONFIG_PATH)


def _load_version_processing_configurations(path: Path) -> dict[str, OLSConfig]:
    with path.open() as file:
        data = json.load(file)
    return {record["prefix"]: OLSConfig.model_validate(record) for record in data["configurations"]}


class OLSAligner(Aligner):
    """Aligner for the OLS."""

    key = "ols"
    getter = get_ols
    curation_header: ClassVar[Sequence[str]] = ("name",)
    include_new = True

    def get_skip(self) -> Mapping[str, str]:
        """Get skipped entries from OLS."""
        return EBI_OLS_SKIP


if __name__ == "__main__":
    OLSAligner.cli()
