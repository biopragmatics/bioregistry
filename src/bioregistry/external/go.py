# -*- coding: utf-8 -*-

"""Download the Gene Ontology registry."""

import json

import click
import yaml
from pystow.utils import download

from bioregistry.constants import EXTERNAL

__all__ = [
    "get_go",
]

# Xrefs from GO that aren't generally useful
SKIP = {
    "TO_GIT",
    "OBO_SF_PO",
    "OBO_SF2_PO",
    "OBO_SF2_PECO",
    "PECO_GIT",
    "PO_GIT",
    "PSO_GIT",
    "EO_GIT",
}

# The key is redundant of the value
REDUNDANT = {
    "AspGD": "AspGD_LOCUS",
}

DIRECTORY = EXTERNAL / "go"
DIRECTORY.mkdir(exist_ok=True, parents=True)
RAW_PATH = DIRECTORY / "raw.yml"
PROCESSED_PATH = DIRECTORY / "processed.json"
GO_URL = "https://raw.githubusercontent.com/geneontology/go-site/master/metadata/db-xrefs.yaml"


def get_go(force_download: bool = False):
    """Get the GO registry."""
    if PROCESSED_PATH.exists() and not force_download:
        with PROCESSED_PATH.open() as file:
            return json.load(file)

    download(url=GO_URL, path=RAW_PATH, force=True)
    with RAW_PATH.open() as file:
        entries = yaml.full_load(file)
    entries = [
        entry
        for entry in entries
        if entry["database"] not in SKIP and entry["database"] not in REDUNDANT
    ]
    rv = {entry["database"]: entry for entry in entries}
    with PROCESSED_PATH.open("w") as file:
        json.dump(rv, file, indent=2, sort_keys=True)
    return rv


@click.command()
def main():
    """Reload the GO data."""
    get_go(force_download=True)


if __name__ == "__main__":
    main()
