"""Download the BARTOC registry."""

import json
from collections.abc import Sequence
from pathlib import Path
from typing import Any, ClassVar

from pystow.utils import download
from tqdm import tqdm

from bioregistry.constants import RAW_DIRECTORY, URI_FORMAT_KEY
from bioregistry.license_standardizer import standardize_license

from ..alignment_utils import Aligner
from ...alignment_model import License, Record, dump_records, load_records

__all__ = [
    "BartocAligner",
    "get_bartoc",
]

HERE = Path(__file__).parent.resolve()
RAW_PATH = RAW_DIRECTORY.joinpath("bartoc.jsonl")
PROCESSED_PATH = HERE / "processed.json"
URL = "https://bartoc.org/data/dumps/latest.ndjson"


def get_bartoc(*, force_download: bool = False, force_process: bool = False) -> dict[str, Record]:
    """Get the BARTOC registry.

    :param force_download: If true, forces download. If false and the file is already
        cached, reuses it.

    :returns: The BARTOC registry

    .. seealso::

        https://bartoc.org/
    """
    if PROCESSED_PATH.is_file() and not force_process:
        return load_records(PROCESSED_PATH)

    download(URL, path=RAW_PATH, force=force_download)

    rv = {}
    with RAW_PATH.open() as file:
        for line in file:
            data = json.loads(line)
            prefix = data["uri"][len("http://bartoc.org/en/node/") :]
            rv[prefix] = _process_bartoc_record(prefix, data)

    dump_records(rv, PROCESSED_PATH)
    return rv


def _process_bartoc_record(prefix: str, data: dict[str, Any]) -> Record:
    rv = {
        "description": data.get("definition", {}).get("en", [""])[0].strip('"').strip(),
        "homepage": data.get("url", "").strip(),
        "name": data.get("prefLabel", {}).get("en", "").strip(),
    }
    pattern = data.get("notationPattern")
    if pattern:
        rv["pattern"] = "^" + pattern.strip().lstrip("^").rstrip("$") + "$"

    # FIXME what about external mappings?
    for identifier in data.get("identifier", []):
        if identifier.startswith("http://www.wikidata.org/entity/"):
            rv["wikidata_database"] = identifier[len("http://www.wikidata.org/entity/") :]

    for short_name in data.get("notation", []):
        short_name = short_name.strip()
        if " " in short_name:
            tqdm.write(f"[bartoc:{prefix}] space in abbr.: {short_name}")
        # FIXME what key
        rv.setdefault("short_name", []).append(short_name)

    for license_dict in data.get("license", []):
        license_url = license_dict["uri"].strip()
        license_key = standardize_license(license_url)
        if license_key:
            rv["license"] = License(url=license_url, spdx=license_key)

    uri_pattern = data.get("uriPattern")
    if uri_pattern and "(" in uri_pattern and ")" in uri_pattern:
        left_pos = uri_pattern.find("(")
        right_pos = uri_pattern.find(")")
        rv[URI_FORMAT_KEY] = uri_pattern[:left_pos] + "$1" + uri_pattern[1 + right_pos :]

    return Record.model_validate({k: v for k, v in rv.items() if k and v})


class BartocAligner(Aligner):
    """Aligner for BARTOC."""

    key = "bartoc"
    getter = get_bartoc
    alt_key_match = "short_name"
    curation_header: ClassVar[Sequence[str]] = ["name", "homepage", "description"]


if __name__ == "__main__":
    BartocAligner.cli(["--force-process", "--no-force"])
