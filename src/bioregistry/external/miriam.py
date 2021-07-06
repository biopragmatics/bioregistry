# -*- coding: utf-8 -*-

"""Download registry information from Identifiers.org/MIRIAMs."""

import json

import click
from pystow.utils import download

from bioregistry.data import EXTERNAL

__all__ = [
    "get_miriam",
]

DIRECTORY = EXTERNAL / "miriam"
DIRECTORY.mkdir(exist_ok=True, parents=True)
RAW_PATH = DIRECTORY / "raw.json"
PROCESSED_PATH = DIRECTORY / "processed.json"
MIRIAM_URL = "https://registry.api.identifiers.org/resolutionApi/getResolverDataset"


def get_miriam(force_download: bool = False):
    """Get the MIRIAM registry."""
    if PROCESSED_PATH.exists() and not force_download:
        with PROCESSED_PATH.open() as file:
            return json.load(file)

    download(url=MIRIAM_URL, path=RAW_PATH, force=True)
    with RAW_PATH.open() as file:
        data = json.load(file)

    rv = {record["prefix"]: _process(record) for record in data["payload"]["namespaces"]}
    with PROCESSED_PATH.open("w") as file:
        json.dump(rv, file, indent=2, sort_keys=True)
    return rv


def _process(record):
    rv = {
        "prefix": record["prefix"],
        "id": record["mirId"][len("MIR:") :],
        "name": record["name"],
        "deprecated": record["deprecated"],
        "namespaceEmbeddedInLui": record["namespaceEmbeddedInLui"],
        "sampleId": record["sampleId"],
        "description": record["description"],
        "pattern": record["pattern"],
    }
    resources = record.get("resources", [])
    has_official = any(resource["official"] for resource in resources)
    if has_official:
        for resource in resources:
            if not resource["official"]:
                continue
            rv["homepage"] = resource["resourceHomeUrl"]
            rv["provider_url"] = resource["urlPattern"].replace("{$id}", "$1")
            break
    else:
        for resource in resources:
            homepage = resource.get("resourceHomeUrl")
            if homepage:
                rv["homepage"] = homepage
            url = resource.get("urlPattern")
            if url:
                rv["provider_url"] = url.replace("{$id}", "$1")
    return rv


@click.command()
def main():
    """Reload the MIRIAM data."""
    r = get_miriam(force_download=True)
    click.echo(f"Got {len(r)} results")


if __name__ == "__main__":
    main()
