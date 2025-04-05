"""Download the Cellosaurus registry."""

from __future__ import annotations

import itertools as itt
import json
import logging
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any, ClassVar

from pystow.utils import download

from bioregistry.constants import RAW_DIRECTORY, URI_FORMAT_KEY
from bioregistry.external.alignment_utils import Aligner, load_processed

__all__ = [
    "CellosaurusAligner",
    "get_cellosaurus",
]

logger = logging.getLogger(__name__)

URL = "https://ftp.expasy.org/databases/cellosaurus/cellosaurus_xrefs.txt"
DIRECTORY = Path(__file__).parent.resolve()
RAW_PATH = RAW_DIRECTORY / "cellosaurus.txt"
PROCESSED_PATH = DIRECTORY / "processed.json"
KEYMAP = {
    "Abbrev": "prefix",
    "Cat": "category",
    "Db_URL": URI_FORMAT_KEY,
    "Name": "name",
    "Server": "homepage",
}


def get_cellosaurus(
    force_download: bool = False, keep_missing_uri: bool = True
) -> dict[str, dict[str, Any]]:
    """Get the Cellosaurus registry."""
    if PROCESSED_PATH.exists() and not force_download:
        return load_processed(PROCESSED_PATH)

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
        d: dict[str, str] = {}
        for line in slines:
            if line[6] != ":":  # strip notes out
                continue
            key, value = (s.strip() for s in line.split(":", 1))
            mapped_key = KEYMAP.get(key)
            if mapped_key is None:
                continue
            if mapped_key == URI_FORMAT_KEY:
                value_tmp = _process_db_url(d["prefix"], value)
                if value_tmp is None:
                    continue
                else:
                    value = value_tmp
            d[mapped_key] = value
        if not keep_missing_uri and URI_FORMAT_KEY not in d:
            continue
        rv[d.pop("prefix")] = d

    with PROCESSED_PATH.open("w") as file:
        json.dump(rv, file, indent=2, sort_keys=True)

    return rv


def _process_db_url(key: str, value: str) -> str | None:
    if value in {"https://%s", "None"}:
        return None
    if value.endswith("http%253A%252F%252Fpurl.obolibrary.org%252Fobo%252F%s") or value.endswith(
        "http://purl.obolibrary.org/obo/%s"
    ):
        logger.debug(
            "Cellosaurus curated an OBO PURL for `%s` that is is missing namespace. "
            "See discussion at https://github.com/biopragmatics/bioregistry/issues/1259.",
            key,
        )
        return None
    return value.rstrip("/").replace("%s", "$1")


class CellosaurusAligner(Aligner):
    """Aligner for the Cellosaurus."""

    key = "cellosaurus"
    getter = get_cellosaurus
    curation_header: ClassVar[Sequence[str]] = ["name", "homepage", "category", URI_FORMAT_KEY]

    def get_skip(self) -> Mapping[str, str]:
        """Get the skipped Cellosaurus identifiers."""
        return {
            "CCTCC": "dead site",
            "CCLV": "stub website, URL dead",
        }


if __name__ == "__main__":
    CellosaurusAligner.cli()
