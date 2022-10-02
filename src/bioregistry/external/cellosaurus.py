# -*- coding: utf-8 -*-

"""Download the Cellosaurus registry."""

import itertools as itt
import json

from pystow.utils import download

from bioregistry.constants import EXTERNAL, URI_FORMAT_KEY

URL = "https://ftp.expasy.org/databases/cellosaurus/cellosaurus_xrefs.txt"

DIRECTORY = EXTERNAL / "cellosaurus"
DIRECTORY.mkdir(exist_ok=True, parents=True)
RAW_PATH = DIRECTORY / "raw.txt"
PROCESSED_PATH = DIRECTORY / "processed.json"
KEYMAP = {
    "Abbrev": "prefix",
    "Cat": "category",
    "Db_URL": URI_FORMAT_KEY,
    "Name": "name",
    "Server": "homepage",
}


def get_cellosaurus(force_download: bool = False, keep_missing_uri: bool = True):
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
            mapped_key = KEYMAP.get(key)
            if mapped_key is None:
                continue
            if mapped_key == URI_FORMAT_KEY:
                value = _process_db_url(value)
                if value is None:
                    continue
            d[mapped_key] = value
        if not keep_missing_uri and URI_FORMAT_KEY not in d:
            continue
        rv[d.pop("prefix")] = d

    with PROCESSED_PATH.open("w") as file:
        json.dump(rv, file, indent=2, sort_keys=True)

    return rv


def _process_db_url(value):
    if value in {"https://%s", "None"}:
        return
    return value.rstrip("/").replace("%s", "$1")


if __name__ == "__main__":
    print(len(get_cellosaurus(force_download=True)))  # noqa:T201
