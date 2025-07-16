"""Download BioContext."""

import json
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import ClassVar

from pystow.utils import download

from bioregistry.alignment_model import Record, dump_records, load_records
from bioregistry.constants import RAW_DIRECTORY, URI_FORMAT_KEY
from bioregistry.external.alignment_utils import Aligner

__all__ = [
    "BioContextAligner",
    "get_biocontext",
]

DIRECTORY = Path(__file__).parent.resolve()
RAW_PATH = RAW_DIRECTORY / "biocontext.json"
PROCESSED_PATH = DIRECTORY / "processed.json"
URL = "https://raw.githubusercontent.com/prefixcommons/biocontext/master/registry/commons_context.jsonld"
SKIP_PARTS = {"identifiers.org", "purl.obolibrary.org"}


def get_biocontext(*, force_download: bool = False) -> Mapping[str, Record]:
    """Get the BioContext context map.

    :param force_download: If true, forces download. If false and the file is already
        cached, reuses it.

    :returns: The biocontext data dictionary

    .. seealso::

        https://github.com/prefixcommons/biocontext
    """
    if PROCESSED_PATH.exists() and not force_download:
        return load_records(PROCESSED_PATH)
    download(url=URL, path=RAW_PATH, force=force_download)
    with RAW_PATH.open() as file:
        data = json.load(file)
    rv = {
        prefix: Record(uri_format=f"{uri_prefix.strip()}$1")
        for prefix, uri_prefix in data["@context"].items()
        if any(p in uri_prefix for p in SKIP_PARTS)
    }
    dump_records(rv, PROCESSED_PATH)
    return rv


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
