"""Download the AberOWL registry."""

from collections.abc import Sequence
from pathlib import Path
from typing import Any, ClassVar

import yaml
from pystow.utils import download
from tqdm import tqdm

from bioregistry.alignment_model import Artifact, ArtifactType, Record, dump_records, load_records
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

SKIP = {"vfdsad": "test", "dlgkj": "test", "hi": "test", "zinnane": "test", "alperk": "test"}


def get_aberowl(*, force_download: bool = False, force_process: bool = False) -> dict[str, Record]:
    """Get the AberOWL registry."""
    if PROCESSED_PATH.exists() and not force_process:
        return load_records(PROCESSED_PATH)

    download(url=ABEROWL_URL, path=RAW_PATH, force=force_download)
    with RAW_PATH.open() as file:
        entries = yaml.full_load(file)

    rv = {entry["acronym"]: record for entry in entries if (record := _process(entry)) is not None}
    dump_records(rv, PROCESSED_PATH)
    return rv


def _process(entry: dict[str, Any]) -> Record | None:
    prefix = entry["acronym"]
    rv = {
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
        elif download_url_suffix.endswith(".skos") or download_url_suffix.endswith(".umls"):
            pass
            # tqdm.write(f"[aberowl:{prefix}] download URL not implemented: {download_url_suffix}")
        else:
            tqdm.write(f"[aberowl:{prefix}] unknown download URL: {download_url_suffix}")

    else:
        return None
    # throw away empty values
    rv = {k: v for k, v in rv.items() if k and v}

    return Record.model_validate(rv)


class AberOWLAligner(Aligner):
    """Aligner for AberOWL."""

    key = "aberowl"
    getter = get_aberowl
    curation_header: ClassVar[Sequence[str]] = ["name", "homepage", "description"]


if __name__ == "__main__":
    AberOWLAligner.cli()
