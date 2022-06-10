# -*- coding: utf-8 -*-

"""Download registry information from the SciCrunch.

.. seealso::

    In this tweet, Anita Bandrowski linked to the registry of resources
    in RRID, but not the namespaces it mints (https://twitter.com/Anitabandrowski/status/1384254551713222659)
"""

import json
import logging

import click
import yaml
from pystow.utils import download

from bioregistry.constants import EXTERNAL

__all__ = [
    "get_scicrunch",
]

logger = logging.getLogger(__name__)

DIRECTORY = EXTERNAL / "scicrunch"
DIRECTORY.mkdir(exist_ok=True, parents=True)
RAW_PATH = DIRECTORY / "raw.yaml"
PROCESSED_PATH = DIRECTORY / "processed.json"
OBOFOUNDRY_URL = "https://scicrunch.org/php/data-federation-csv.php?orMultiFacets=true&sortField=Proper%20Citation&sortAsc=true&q=%2A&sortField=Proper%20Citation&sortAsc=true&q=%2A&count=1000&orMultiFacets=true&nifid=nlx_144509-1&exportType=data"


def get_scicrunch(force_download: bool = False):
    """Get the OBO Foundry registry."""
    if PROCESSED_PATH.exists() and not force_download:
        with PROCESSED_PATH.open() as file:
            return json.load(file)

    download(url=OBOFOUNDRY_URL, path=RAW_PATH, force=True)
    with RAW_PATH.open() as file:
        data = yaml.full_load(file)

    rv = {record["id"]: _process(record) for record in data["ontologies"]}
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


@click.command()
def main():
    """Reload the SciCrunch data."""
    r = get_scicrunch(force_download=True)
    click.echo(f"Got {len(r)} records")


if __name__ == "__main__":
    main()
