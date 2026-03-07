"""Download BioContext, see https://github.com/prefixcommons/biocontext."""

import json
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import ClassVar

from bioregistry.alignment_model import Record
from bioregistry.constants import RAW_DIRECTORY, URI_FORMAT_KEY
from bioregistry.external.alignment_utils import Aligner, build_getter

__all__ = [
    "BioContextAligner",
    "get_biocontext",
    "parse_biocontext_raw",
]

DIRECTORY = Path(__file__).parent.resolve()
RAW_PATH = RAW_DIRECTORY / "biocontext.json"
PROCESSED_PATH = DIRECTORY / "processed.json"
URL = "https://raw.githubusercontent.com/prefixcommons/biocontext/master/registry/commons_context.jsonld"
SKIP_PARTS = {"identifiers.org", "purl.obolibrary.org"}


def parse_biocontext_raw(path: Path) -> dict[str, Record]:
    """Parse BioContext JSON file."""
    with path.open() as file:
        data = json.load(file)
    rv = {
        prefix: Record(uri_format=f"{uri_prefix.strip()}$1")
        for prefix, uri_prefix in data["@context"].items()
        if any(p in uri_prefix for p in SKIP_PARTS)
    }
    return rv


get_biocontext = build_getter(
    processed_path=PROCESSED_PATH,
    url=URL,
    raw_path=RAW_PATH,
    func=parse_biocontext_raw,
)


class BioContextAligner(Aligner):
    """Aligner for BioContext."""

    key = "biocontext"
    getter = get_biocontext
    curation_header: ClassVar[Sequence[str]] = [URI_FORMAT_KEY]

    def get_skip(self) -> Mapping[str, str]:
        """Get entries for BioContext that should be skipped."""
        return {
            "fbql": "not a real resource, as far as I can tell",
        }


if __name__ == "__main__":
    BioContextAligner.cli()
