"""Download registry information from Pathguide."""

from collections.abc import Sequence
from pathlib import Path
from typing import ClassVar

from bs4 import BeautifulSoup

from bioregistry.alignment_model import Record, make_record
from bioregistry.constants import RAW_DIRECTORY
from bioregistry.external.alignment_utils import Aligner, build_getter

__all__ = [
    "PathguideAligner",
    "get_pathguide",
]

PROCESSED_PATH = Path(__file__).parent / "processed.json"
RAW_PATH = RAW_DIRECTORY.joinpath("pathguide.html")
URL = "http://pathguide.org/"


def process_pathguide(path: Path) -> dict[str, Record]:
    """Process Pathguide."""
    with path.open() as f:
        soup = BeautifulSoup(f.read(), "html.parser")
    rv = {}
    for tr in soup.find_all("tr"):
        tr_id = tr.attrs.get("id")
        if not tr_id or not tr_id.startswith("ResourceRow_"):
            continue
        pathguide_id = tr_id.removeprefix("ResourceRow_")
        name_td, _, _availability_td, standards_td = list(tr)
        name_a = name_td.find("a")
        homepage = name_a.attrs["href"]
        abbreviation, name = (s.strip() for s in name_a.text.split(" - ", 1))
        standards = sorted(
            {td.text for td in standards_td.find_all("td") if td.attrs.get("class") == ["Standard"]}
        )
        dd = {
            "prefix": pathguide_id,
            "short_names": [abbreviation],
            "name": name,
            "homepage": homepage,
        }
        if standards:
            dd["keywords"] = standards

        rv[pathguide_id] = make_record(dd)
    return rv


get_pathguide = build_getter(
    processed_path=PROCESSED_PATH,
    raw_path=RAW_PATH,
    url=URL,
    func=process_pathguide,
)


class PathguideAligner(Aligner):
    """Aligner for the Pathguide."""

    key = "pathguide"
    alt_key_match = "abbreviation"
    getter = get_pathguide
    curation_header: ClassVar[Sequence[str]] = ("abbreviation", "name", "homepage")


if __name__ == "__main__":
    PathguideAligner.cli()
