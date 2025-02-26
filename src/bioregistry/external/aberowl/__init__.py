"""Download the AberOWL registry."""

import json
from pathlib import Path
from typing import Any

import yaml
from pystow.utils import download

from bioregistry.constants import RAW_DIRECTORY
from bioregistry.external.alignment_utils import Aligner

__all__ = [
    "AberOWLAligner",
    "get_aberowl",
]

DIRECTORY = Path(__file__).parent.resolve()
RAW_PATH = RAW_DIRECTORY / "aberowl.json"
PROCESSED_PATH = DIRECTORY / "processed.json"
ABEROWL_URL = "http://aber-owl.net/api/ontology/?drf_fromat=json&format=json"


def get_aberowl(force_download: bool = False) -> dict[str, dict[str, Any]]:
    """Get the AberOWL registry."""
    if PROCESSED_PATH.exists() and not force_download:
        with PROCESSED_PATH.open() as file:
            return json.load(file)

    download(url=ABEROWL_URL, path=RAW_PATH, force=True)
    with RAW_PATH.open() as file:
        entries = yaml.full_load(file)
    rv = {entry["acronym"]: _process(entry) for entry in entries}
    with PROCESSED_PATH.open("w") as file:
        json.dump(rv, file, indent=2, sort_keys=True)
    return rv


def _process(entry: dict[str, Any]) -> dict[str, str]:
    rv = {
        "prefix": entry["acronym"],
        "name": entry["name"],
    }
    submission = entry.get("submission", {})
    if submission:
        rv["homepage"] = submission.get("home_page")

        description = submission.get("description")
        if description:
            description = (
                description.strip().replace("\r\n", " ").replace("\n", " ").replace("  ", " ")
            )
            rv["description"] = description
        version = submission.get("version")
        if version:
            rv["version"] = version.strip()
        download_url_suffix = submission.get("download_url")
        if not download_url_suffix:
            pass
        elif download_url_suffix.endswith(".owl"):
            rv["download_owl"] = f"http://aber-owl.net/{download_url_suffix}"
        elif download_url_suffix.endswith(".obo"):
            rv["download_obo"] = f"http://aber-owl.net/{download_url_suffix}"
        else:
            pass  # what's going on here?
    return {k: v for k, v in rv.items() if k and v}


class AberOWLAligner(Aligner):
    """Aligner for AberOWL."""

    key = "aberowl"
    getter = get_aberowl
    curation_header = ["name", "homepage", "description"]


if __name__ == "__main__":
    AberOWLAligner.cli()
