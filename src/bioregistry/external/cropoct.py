# -*- coding: utf-8 -*-

"""Download registry information from CROPOCT."""

import io
import json
import logging

import click
import yaml
from pystow.utils import download

from bioregistry.constants import EXTERNAL

__all__ = [
    "get_cropoct",
]

logger = logging.getLogger(__name__)

DIRECTORY = EXTERNAL / "cropoct"
DIRECTORY.mkdir(exist_ok=True, parents=True)
RAW_PATH = DIRECTORY / "raw.yaml"
PROCESSED_PATH = DIRECTORY / "processed.json"
CROPOCT_URL = "https://cropontology.org/metadata"


def get_cropoct(force_download: bool = False):
    """Get the CropOCT registry."""
    if PROCESSED_PATH.exists() and not force_download:
        with PROCESSED_PATH.open() as file:
            return json.load(file)

    download(url=CROPOCT_URL, path=RAW_PATH, force=True)

    lines = []
    with RAW_PATH.open() as file:
        next(file)  # throw away header
        for i, line in enumerate(file):
            line = line.rstrip()
            line = line.replace(" : ", ": ")
            if line.count('"') > 2:
                logger.debug("issue on line %s: %s", i, line)
                continue
            lines.append(line)

    fixed = "\n".join(lines)
    RAW_PATH.write_text(
        yaml.safe_dump(
            yaml.safe_load(io.StringIO(fixed)),
            indent=2,
        )
    )
    with RAW_PATH.open() as file:
        data = yaml.safe_load(file)

    rv = {record["id"]: _process(record) for record in data["ontologies"]}
    with PROCESSED_PATH.open("w") as file:
        json.dump(rv, file, indent=2, sort_keys=True)
    return rv


def _process(record):
    rv = {
        "prefix": record["id"],
        "name": record["title"],
        "homepage": record["homepage"],
        "download_owl": record.get("ontology_purl"),
        "description": record.get("description"),
    }
    return {k: v for k, v in rv.items() if k and v}


if __name__ == "__main__":
    click.echo(len(get_cropoct(force_download=True)))
