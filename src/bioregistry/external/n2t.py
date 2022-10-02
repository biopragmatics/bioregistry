# -*- coding: utf-8 -*-

"""Download registry information from N2T."""

import json

import click
import yaml
from pystow.utils import download

from bioregistry.constants import EXTERNAL, URI_FORMAT_KEY

URL = "https://n2t.net/e/n2t_full_prefixes.yaml"
DIRECTORY = EXTERNAL / "n2t"
DIRECTORY.mkdir(exist_ok=True, parents=True)
RAW_PATH = DIRECTORY / "raw.yml"
PROCESSED_PATH = DIRECTORY / "processed.json"
SKIP = {
    "zzztestprefix": "test prefix should not be considered",
    "urn": "too meta",
    "url": "too meta",
    "purl": "too meta",
    "lsid": "too meta",
    "hdl": "paid service, too meta",
    "repec": "irrelevant prefix from economics",
    "merops": "issue with miriam having duplicate prefixes for this resource",  # FIXME
    "hgnc.family": "issue with miriam having duplicate prefixes for this resource",  # FIXME
}


def get_n2t(force_download: bool = False):
    """Get the N2T registry."""
    if PROCESSED_PATH.exists() and not force_download:
        with PROCESSED_PATH.open() as file:
            return json.load(file)

    download(url=URL, path=RAW_PATH, force=True)
    # they give malformed YAML so time to write a new parser
    with RAW_PATH.open() as file:
        data = yaml.safe_load(file)

    rv = {
        key: _process(record)
        for key, record in data.items()
        if record["type"] == "scheme" and "/" not in key and key not in SKIP
    }

    with PROCESSED_PATH.open("w") as file:
        json.dump(rv, file, sort_keys=True, indent=2)
    return rv


def _process(record):
    rv = {
        "name": record.get("name"),
        URI_FORMAT_KEY: record["redirect"].replace("$id", "$1") if "redirect" in record else None,
        "description": record.get("description"),
        "homepage": record.get("more"),
        "pattern": record.get("pattern"),
        "example": record.get("test"),
        "namespaceEmbeddedInLui": (record.get("prefixed") == "true"),
    }
    return {k: v for k, v in rv.items() if v is not None}


@click.command()
def main():
    """Reload the N2T data."""
    rv = get_n2t(force_download=True)
    click.echo(f"Got {len(rv)} entries from n2t.")


if __name__ == "__main__":
    main()
