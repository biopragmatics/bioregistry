"""Download the AberOWL registry."""

from collections.abc import Sequence
from pathlib import Path
from typing import Any, ClassVar

import yaml
from tqdm import tqdm

from bioregistry.alignment_model import Artifact, ArtifactType, Record, make_record
from bioregistry.constants import RAW_DIRECTORY
from bioregistry.external.alignment_utils import Aligner, build_getter, cleanup_json

__all__ = [
    "AberOWLAligner",
    "get_aberowl",
    "parse_aberowl_raw",
]

DIRECTORY = Path(__file__).parent.resolve()
RAW_PATH = RAW_DIRECTORY / "aberowl.json"
PROCESSED_PATH = DIRECTORY / "processed.json"
ABEROWL_URL = "http://aber-owl.net/api/ontology/?drf_fromat=json&format=json"

SKIP = {
    "vfdsad": "test",
    "dlgkj": "test",
    "hi": "test",
    "zinnane": "test",
    "alperk": "test",
    "x": "stub",
    "acro": "test",
    "a": "spam",
    "cd": "spam",
    "tfernandes": "spam",
}


def parse_aberowl_raw(path: Path) -> dict[str, Record]:
    """Parse the raw AberOWL YAML."""
    with path.open() as file:
        entries = yaml.full_load(file)
    rv = {
        entry["acronym"]: record
        for entry in entries
        if (record := process_aberowl_record(entry)) is not None and entry["acronym"] not in SKIP
    }
    return rv


def process_aberowl_record(entry: dict[str, Any]) -> Record | None:
    """Process a record from AberOWL."""
    prefix = entry["acronym"]
    rv = {
        "name": entry["name"],
    }
    submission = entry.get("submission", {})
    if not submission:
        # TODO return None instead
        return Record.model_validate(rv)

    rv["homepage"] = submission.get("home_page")

    description = submission.get("description")
    if description:
        description = description.strip().replace("\r\n", " ").replace("\n", " ").replace("  ", " ")
        rv["description"] = description
    version = submission.get("version")
    if version:
        rv["version"] = version.strip()
    download_url_suffix = submission.get("download_url")
    if not download_url_suffix:
        pass
    elif download_url_suffix.endswith(".owl"):
        rv.setdefault("artifacts", []).append(
            Artifact(
                url=f"http://aber-owl.net/{download_url_suffix}",
                type=ArtifactType.owl,
            )
        )
    elif download_url_suffix.endswith(".obo"):
        rv.setdefault("artifacts", []).append(
            Artifact(
                url=f"http://aber-owl.net/{download_url_suffix}",
                type=ArtifactType.obo,
            )
        )
    elif download_url_suffix.endswith(".skos"):
        pass  # TODO
    elif download_url_suffix.endswith(".umls"):
        pass  # TODO
    else:
        tqdm.write(f"[aberowl:{prefix}] unknown download URL: {download_url_suffix}")

    return make_record(rv)


get_aberowl = build_getter(
    processed_path=PROCESSED_PATH,
    raw_path=RAW_PATH,
    url=ABEROWL_URL,
    func=parse_aberowl_raw,
    cleanup=cleanup_json,
)


class AberOWLAligner(Aligner):
    """Aligner for AberOWL."""

    key = "aberowl"
    getter = get_aberowl
    curation_header: ClassVar[Sequence[str]] = ["name", "homepage", "description"]


if __name__ == "__main__":
    AberOWLAligner.cli()
