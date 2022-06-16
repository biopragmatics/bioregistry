# -*- coding: utf-8 -*-

"""Download registry information from Identifiers.org/MIRIAMs."""

import json

import click
from pystow.utils import download

from bioregistry.constants import EXTERNAL, URI_FORMAT_KEY

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
    resources = [
        _preprocess_resource(resource)
        for resource in record.get("resources", [])
        if not resource.get("deprecated")
    ]
    if not resources:
        return rv

    has_official = any(resource["official"] for resource in resources)
    if has_official:
        primary = next(resource for resource in resources if resource["official"])
        rest = [resource for resource in resources if not resource["official"]]
    else:
        primary, *rest = resources
    rv["homepage"] = primary["homepage"]
    rv[URI_FORMAT_KEY] = primary[URI_FORMAT_KEY]

    extras = []
    for provider in rest:
        if provider["code"] in SKIP_PROVIDERS:
            continue
        del provider["official"]
        extras.append(provider)
    if extras:
        rv["providers"] = extras
    return rv


#: These provider codes are handled by the Bioregistry's metaregistry
SKIP_PROVIDERS = {
    "ols",
    "bptl",
}


def _preprocess_resource(resource):
    return {
        "official": resource["official"],
        "homepage": resource["resourceHomeUrl"],
        "code": resource["providerCode"],
        URI_FORMAT_KEY: resource["urlPattern"].replace("{$id}", "$1"),
        "name": resource["name"],
        "description": resource["description"],
    }


@click.command()
def main():
    """Reload the MIRIAM data."""
    r = get_miriam(force_download=True)
    click.echo(f"Got {len(r)} results")


if __name__ == "__main__":
    main()
