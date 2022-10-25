# -*- coding: utf-8 -*-

"""Download registry information from the OBO Foundry."""

import json
import logging
from typing import Optional

import click
import requests
import yaml
from pystow.utils import download

from bioregistry.constants import EXTERNAL

__all__ = [
    "get_obofoundry",
    "get_obofoundry_example",
]

logger = logging.getLogger(__name__)

DIRECTORY = EXTERNAL / "obofoundry"
DIRECTORY.mkdir(exist_ok=True, parents=True)
RAW_PATH = DIRECTORY / "raw.yaml"
PROCESSED_PATH = DIRECTORY / "processed.json"
OBOFOUNDRY_URL = "https://raw.githubusercontent.com/OBOFoundry/OBOFoundry.github.io/master/registry/ontologies.yml"
SKIP = {
    "obo_rel": "replaced",
}


def get_obofoundry(force_download: bool = False):
    """Get the OBO Foundry registry."""
    if PROCESSED_PATH.exists() and not force_download:
        with PROCESSED_PATH.open() as file:
            return json.load(file)

    download(url=OBOFOUNDRY_URL, path=RAW_PATH, force=True)
    with RAW_PATH.open() as file:
        data = yaml.full_load(file)

    rv = {
        record["id"]: _process(record) for record in data["ontologies"] if record["id"] not in SKIP
    }
    for key, record in rv.items():
        for depends_on in record.get("depends_on", []):
            if depends_on not in rv:
                logger.warning("issue in %s: invalid dependency: %s", key, depends_on)
            else:
                rv[depends_on].setdefault("appears_in", []).append(key)
    with PROCESSED_PATH.open("w") as file:
        json.dump(rv, file, indent=2, sort_keys=True, ensure_ascii=False)

    return rv


def _process(record):
    for key in ("browsers", "usages", "depicted_by", "build", "layout", "taxon"):
        if key in record:
            del record[key]

    oid = record["id"].lower()
    rv = {
        "name": record["title"],
        "description": record.get("description"),
        "deprecated": record["activity_status"] != "active",
        "homepage": record.get("homepage") or record.get("repository"),
        "preferredPrefix": record.get("preferredPrefix"),
        "license": record.get("license", {}).get("label"),
        "license.url": record.get("license", {}).get("url"),
        "contact": record.get("contact", {}).get("email"),
        "contact.label": record.get("contact", {}).get("label"),
        "contact.github": record.get("contact", {}).get("github"),
        "contact.orcid": record.get("contact", {}).get("orcid"),
        "repository": record.get("repository"),
        "domain": record.get("domain"),
    }

    for key in ("publications", "twitter"):
        value = record.get(key)
        if value:
            rv[key] = value

    dependencies = record.get("dependencies")
    if dependencies:
        rv["depends_on"] = sorted(
            dependency["id"]
            for dependency in record.get("dependencies", [])
            if dependency.get("type") not in {"BridgeOntology"}
        )

    for product in record.get("products", []):
        if product["id"] == f"{oid}.obo":
            rv["download.obo"] = product["ontology_purl"]
        elif product["id"] == f"{oid}.json":
            rv["download.json"] = product["ontology_purl"]
        elif product["id"] == f"{oid}.owl":
            rv["download.owl"] = product["ontology_purl"]

    return {k: v for k, v in rv.items() if v is not None}


def get_obofoundry_example(prefix: str) -> Optional[str]:
    """Get an example identifier from the OBO Library PURL configuration."""
    url = f"https://raw.githubusercontent.com/OBOFoundry/purl.obolibrary.org/master/config/{prefix}.yml"
    data = yaml.safe_load(requests.get(url).content)
    examples = data.get("example_terms")
    if not examples:
        return None
    return examples[0].rsplit("_")[-1]


@click.command()
def main():
    """Reload the OBO Foundry data."""
    r = get_obofoundry(force_download=True)
    click.echo(f"Got {len(r)} records")


if __name__ == "__main__":
    main()
