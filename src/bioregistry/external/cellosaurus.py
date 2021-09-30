# -*- coding: utf-8 -*-

"""Download the Cellosaurus registry."""

import itertools as itt
import json

import click
from pystow.utils import download

from bioregistry.data import EXTERNAL

URL = "https://ftp.expasy.org/databases/cellosaurus/cellosaurus_xrefs.txt"

DIRECTORY = EXTERNAL / "cellosaurus"
DIRECTORY.mkdir(exist_ok=True, parents=True)
RAW_PATH = DIRECTORY / "raw.txt"
PROCESSED_PATH = DIRECTORY / "processed.json"
KEYMAP = {
    "Abbrev": "prefix",
    "Cat": "category",
    "Db_URL": "url",
    "Name": "name",
    "Server": "homepage",
}


def get_cellosaurus(force_download: bool = False):
    """Get the Cellosaurus registry."""
    if PROCESSED_PATH.exists() and not force_download:
        with PROCESSED_PATH.open() as file:
            return json.load(file)

    download(url=URL, path=RAW_PATH, force=True)
    with RAW_PATH.open(encoding="ISO8859-1") as file:
        lines = [line.rstrip() for line in file]

    # Get up until the third big line break and chomp two extra lines
    # for the line break
    break_line_idxs = [i for i, line in enumerate(lines) if line.startswith("------")]
    lines = lines[break_line_idxs[3] + 2 :]

    rv = {}
    for cond, slines in itt.groupby(lines, lambda line: line == "//"):
        if cond:
            continue
        d = {}
        for line in slines:
            if line[6] != ":":  # strip notes out
                continue
            key, value = (s.strip() for s in line.split(":", 1))
            key = KEYMAP[key]
            if key == "url":
                value = _process_db_url(value)
                if value is None:
                    continue
            d[key] = value
        rv[d.pop("prefix")] = d

    with PROCESSED_PATH.open("w") as file:
        json.dump(rv, file, indent=2, sort_keys=True)

    return rv


def _process_db_url(value):
    if value in {"https://%s", "None"}:
        return
    return value.rstrip("/").replace("%s", "$1")


@click.command()
def main():
    """Reload the Cellosaurus data."""
    rv = get_cellosaurus(force_download=True)
    click.echo(f"Got {len(rv)} entries from cellosaurus.")


if __name__ == "__main__":
    main()
