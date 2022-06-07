# -*- coding: utf-8 -*-

"""Download the AberOWL registry."""

import json

import click
import yaml

from bioregistry.constants import EXTERNAL
from pystow.utils import download

__all__ = [
    "get_aberowl",
]

DIRECTORY = EXTERNAL / "aberowl"
DIRECTORY.mkdir(exist_ok=True, parents=True)
RAW_PATH = DIRECTORY / "raw.yml"
PROCESSED_PATH = DIRECTORY / "processed.json"
ABEROWL_URL = "http://aber-owl.net/api/ontology/?drf_fromat=json&format=json"


def get_aberowl(force_download: bool = False):
    """Get the AberOWL registry."""
    if PROCESSED_PATH.exists() and not force_download:
        with PROCESSED_PATH.open() as file:
            return json.load(file)

    download(url=ABEROWL_URL, path=RAW_PATH, force=True)
    with RAW_PATH.open() as file:
        entries = yaml.full_load(file)
    entries = [
        entry
        for entry in entries
        # if entry["database"] not in SKIP and entry["database"] not in REDUNDANT
    ]
    rv = {entry["acronym"]: entry for entry in entries}
    with PROCESSED_PATH.open("w") as file:
        json.dump(rv, file, indent=2, sort_keys=True)
    return rv


@click.command()
def main():
    """Reload the GO data."""
    click.echo(len(get_aberowl(force_download=True)))


if __name__ == "__main__":
    main()
