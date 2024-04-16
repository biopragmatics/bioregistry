# -*- coding: utf-8 -*-

"""Download registry information from Identifiers.org/MIRIAMs."""

import json
from operator import itemgetter

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
SKIP = {
    "merops",
    "hgnc.family",
    # Appear to be unreleased records
    "f82a1a",
    "4503",
    "6vts",
}
SKIP_URI_FORMATS = {
    "http://arabidopsis.org/servlets/TairObject?accession=$1",
}


def get_miriam(force_download: bool = False, force_process: bool = False):
    """Get the MIRIAM registry."""
    if PROCESSED_PATH.exists() and not force_download and not force_process:
        with PROCESSED_PATH.open() as file:
            return json.load(file)

    download(url=MIRIAM_URL, path=RAW_PATH, force=force_download)
    with open(RAW_PATH) as file:
        data = json.load(file)

    data["payload"]["namespaces"] = sorted(data["payload"]["namespaces"], key=itemgetter("prefix"))
    if force_download:
        with open(RAW_PATH, "w") as file:
            json.dump(data, file, indent=2, sort_keys=True, ensure_ascii=False)

    rv = {
        record["prefix"]: _process(record)
        for record in data["payload"]["namespaces"]
        # records whose prefixes start with `dg.` appear to be unreleased
        if not record["prefix"].startswith("dg.") and record["prefix"] not in SKIP
    }
    with PROCESSED_PATH.open("w") as file:
        json.dump(rv, file, indent=2, sort_keys=True)
    return rv


#: Pairs of MIRIAM prefix and provider codes to skip
PROVIDER_BLACKLIST = {
    ("ega.study", "omicsdi"),
    # see discussion at https://github.com/biopragmatics/bioregistry/pull/944
    ("bioproject", "ebi"),
    ("pmc", "ncbi"),
}


def _process(record):
    prefix = record["prefix"]
    rv = {
        "prefix": prefix,
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
    if URI_FORMAT_KEY in primary:
        rv[URI_FORMAT_KEY] = primary[URI_FORMAT_KEY]

    extras = []
    for provider in rest:
        code = provider["code"]
        if code in SKIP_PROVIDERS or (prefix, code) in PROVIDER_BLACKLIST:
            continue
        del provider["official"]
        extras.append(provider)
    if extras:
        rv["providers"] = extras
    return rv


SKIP_PROVIDERS = {
    "ols",  # handled by the Bioregistry's metaregistry
    "bptl",  # handled by the Bioregistry's metaregistry
    "bioentitylink",
}


def _preprocess_resource(resource):
    rv = {
        "official": resource["official"],
        "homepage": resource["resourceHomeUrl"],
        "code": resource["providerCode"],
        "name": resource["name"],
        "description": resource["description"],
    }
    uri_format = resource["urlPattern"].replace("{$id}", "$1")
    if uri_format not in SKIP_URI_FORMATS:
        rv[URI_FORMAT_KEY] = uri_format
    return rv


@click.command()
def main():
    """Reload the MIRIAM data."""
    r = get_miriam(force_download=True)
    click.echo(f"Got {len(r)} results")


if __name__ == "__main__":
    main()
