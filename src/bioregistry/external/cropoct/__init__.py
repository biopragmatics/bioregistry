"""Download registry information from CROPOCT."""

import io
import logging
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any, ClassVar

import yaml

from bioregistry.alignment_model import Record, make_record
from bioregistry.constants import RAW_DIRECTORY
from bioregistry.external.alignment_utils import Aligner, build_getter

__all__ = [
    "CropOCTAligner",
    "get_cropoct",
    "process_cropoct_raw",
]

logger = logging.getLogger(__name__)

DIRECTORY = Path(__file__).parent.resolve()
RAW_PATH = RAW_DIRECTORY / "cropoct.yaml"
PROCESSED_PATH = DIRECTORY / "processed.json"
CROPOCT_URL = "https://cropontology.org/metadata"


def process_cropoct_raw(path: Path) -> dict[str, Record]:
    """Parse CropOCT raw JSON."""
    with path.open() as file:
        data = yaml.safe_load(file)
    rv = {record["id"]: _process(record) for record in data["ontologies"]}
    return rv


def _cleanup(path: Path) -> None:
    lines = []
    with path.open() as file:
        for i, line in enumerate(file):
            line = line.rstrip()
            line = line.replace(" : ", ": ")
            if line.count('"') > 2:
                logger.debug("issue on line %s: %s", i, line)
                continue
            lines.append(line)

    fixed = "\n".join(lines)
    path.write_text(
        yaml.safe_dump(
            yaml.safe_load(io.StringIO(fixed)),
            indent=2,
        )
    )


def _process(record: Mapping[str, Any]) -> Record:
    rv = {
        "name": record["title"],
        "homepage": record["homepage"],
        "description": record.get("description"),
    }
    if owl_url := record.get("ontology_purl"):
        rv["artifacts"] = [
            {
                "type": "owl",
                "url": owl_url,
            }
        ]
    return make_record(rv)


get_cropoct = build_getter(
    processed_path=PROCESSED_PATH,
    raw_path=RAW_PATH,
    url=CROPOCT_URL,
    func=process_cropoct_raw,
    cleanup=_cleanup,
)


class CropOCTAligner(Aligner):
    """Aligner for CropOCT."""

    key = "cropoct"
    getter = get_cropoct
    curation_header: ClassVar[Sequence[str]] = ["name", "homepage", "description"]


if __name__ == "__main__":
    CropOCTAligner.cli()
