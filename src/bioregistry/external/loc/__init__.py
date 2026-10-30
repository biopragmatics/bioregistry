"""Align LOC Class Schemes."""

from pathlib import Path

from pystow.utils import get_xml_root

from bioregistry.alignment_model import Record, dump_records, load_processed
from bioregistry.external.alignment_utils import Aligner, adapter

__all__ = [
    "LOCAligner",
    "get_loc",
]

HERE = Path(__file__).parent.resolve()
RAW_PATH = HERE.joinpath("OID_Report.csv")
PROCESSED_PATH = HERE.joinpath("processed.json")

URL = "https://id.loc.gov/vocabulary/classSchemes.rdf"
XPATH_QUERY = (
    ".//{http://www.loc.gov/mads/rdf/v1#}hasMADSSchemeMember"
    "/{http://www.loc.gov/mads/rdf/v1#}Authority"
)
URI_PREFIX = "http://id.loc.gov/vocabulary/classSchemes/"


@adapter
def get_loc(
    *, force_download: bool = False, force_process: bool = False, progress: bool = True
) -> dict[str, Record]:
    """Get LOC Class Scheme records."""
    if PROCESSED_PATH.exists() and not force_download and not force_process:
        return load_processed(PROCESSED_PATH)
    rv = _get_records()
    dump_records(rv, PROCESSED_PATH)
    return rv


def _get_records() -> dict[str, Record]:
    """Get LOC Class Scheme records."""
    records = {}
    root = get_xml_root(URL)
    for authority in root.iterfind(XPATH_QUERY):
        uri = authority.attrib["{http://www.w3.org/1999/02/22-rdf-syntax-ns#}about"]
        prefix = uri.removeprefix(URI_PREFIX)
        label = authority.findtext("{http://www.loc.gov/mads/rdf/v1#}authoritativeLabel")
        records[prefix] = Record(name=label)
    return records


class LOCAligner(Aligner):
    """Aligner for LOC Class Schemes."""

    key = "loc.classschemes"
    getter = get_loc


if __name__ == "__main__":
    LOCAligner.cli()
