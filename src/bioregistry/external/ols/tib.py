"""Download and align against the TIB Terminology Service."""

from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import ClassVar

from bioregistry.constants import RAW_DIRECTORY
from bioregistry.external.alignment_utils import Aligner
from bioregistry.external.ols import OlsRv, get_ols_base

HERE = Path(__file__).parent.resolve()
RAW_PATH = RAW_DIRECTORY.joinpath("tib.json")
PROCESSED_PATH = HERE.joinpath("tib-processed.json")
VERSION_PROCESSING_CONFIG_PATH = HERE.joinpath("tib-processing-config.json")
TIB_OLS_BASE_URL = "https://api.terminology.tib.eu/api"

__all__ = [
    "TIBAligner",
    "get_tib_ts",
]

SKIP = {
    "bflc": "",
    "envo2021": "",
    "envo2023": "",
    "ordo40": "",
    "ordo41": "",
    "ordo42": "",
    "ordo46": "",
    "ordo47": "",
    "nmrcv2025": "",
    "dfgfo2024": "",
    "hoom": "not sure this is its own ontology",
    "zbwext": "not sure this is its own ontology",
    "oboe-characteristics": "duplicate of top level",  # todo reinvestigate
    "oboe-standards": "duplicate of top level",
    "sds": "this is not a semantic space! the RDF document linked on TIB is a description of the standard itself",
}


def get_tib_ts(*, force_download: bool = False) -> OlsRv:
    """Get the TIB Terminology Service."""
    return get_ols_base(
        force_download=force_download,
        base_url=TIB_OLS_BASE_URL,
        processed_path=PROCESSED_PATH,
        raw_path=RAW_PATH,
        version_processing_config_path=VERSION_PROCESSING_CONFIG_PATH,
        skip_uri_format={"edam"},
    )


class TIBAligner(Aligner):
    """Aligner for the TIB Terminology Service."""

    key = "tib"
    getter = get_tib_ts
    curation_header: ClassVar[Sequence[str]] = ("name",)
    include_new = True

    def get_skip(self) -> Mapping[str, str]:
        """Get skips."""
        return SKIP


if __name__ == "__main__":
    TIBAligner.cli()
