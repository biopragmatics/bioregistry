# -*- coding: utf-8 -*-

"""Download registry information from the OLS."""

import datetime
import json
import logging
from email.utils import parseaddr
from textwrap import dedent
from typing import Any, Mapping, Optional

import click
from pystow.utils import download

from bioregistry.data import EXTERNAL, OLSConfig, get_ols_processing

__all__ = [
    "get_ols",
]

logger = logging.getLogger(__name__)

DIRECTORY = EXTERNAL / "ols"
DIRECTORY.mkdir(exist_ok=True, parents=True)
URL = "https://www.ebi.ac.uk/ols/api/ontologies?size=1000"
RAW_PATH = DIRECTORY / "raw.json"
PROCESSED_PATH = DIRECTORY / "processed.json"

_PROCESSING = get_ols_processing()


def get_ols(force_download: bool = False):
    """Get the OLS registry."""
    if PROCESSED_PATH.exists() and not force_download:
        with PROCESSED_PATH.open() as file:
            return json.load(file)

    download(url=URL, path=RAW_PATH, force=True)
    with RAW_PATH.open() as file:
        data = json.load(file)

    if "next" in data["_links"]:
        raise NotImplementedError(
            "Need to implement paging since there are more entries than fit into one page"
        )

    processed = {}
    for ontology in data["_embedded"]["ontologies"]:
        ols_id = ontology["ontologyId"]
        # TODO better docs on how to maintain this file
        config = _PROCESSING.get(ols_id)
        if config is None:
            logger.warning("need to curate processing file for OLS prefix %s", ols_id)
            continue
        processed[ols_id] = _process(ontology, config)

    with PROCESSED_PATH.open("w") as file:
        json.dump(processed, file, indent=2, sort_keys=True)
    return processed


def _process(ols_entry: Mapping[str, Any], processing: OLSConfig) -> Optional[Mapping[str, str]]:
    ols_id = ols_entry["ontologyId"]
    config = ols_entry["config"]
    version_iri = config["versionIri"]
    rv = {
        "prefix": ols_id,
        "name": config["title"],
        "download": _clean_url(config["fileLocation"]),
        "version.iri": _clean_url(version_iri),
        "description": config["description"],
        "homepage": _clean_url(config["homepage"]),
    }

    email = config.get("mailingList")
    if email:
        name, email = parseaddr(email)
        if email.startswith("//"):
            logger.debug("[%s] invalid email address: %s", ols_id, config["mailingList"])
        else:
            rv["contact"] = email

    license_value = config.get("annotations", {}).get("license", [None])[0]
    if license_value in {"Unspecified", "Unspecified"}:
        license_value = None
    if not license_value:
        logger.info("[%s] missing license in OLS. Contact: %s", ols_id, config["mailingList"])
    rv["license"] = license_value

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

    rv["version"] = version

    rv = {k: v for k, v in rv.items() if v}
    return rv


def _clean_url(url: Optional[str]) -> Optional[str]:
    if url is None:
        return url
    if "CO_" in url and url.startswith("http://127.0.0.1:5900"):
        return "https://cropontology.org" + url[len("http://127.0.0.1:5900") :]
    return url


@click.command()
def main():
    """Reload the OLS data."""
    get_ols(force_download=True)


if __name__ == "__main__":
    main()
