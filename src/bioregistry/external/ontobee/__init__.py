"""Download registry information from OntoBee."""

import textwrap
from collections.abc import Sequence
from pathlib import Path
from typing import Any, ClassVar

from bs4 import BeautifulSoup

from bioregistry.alignment_model import Record, make_record
from bioregistry.constants import RAW_DIRECTORY
from bioregistry.external.alignment_utils import Aligner, build_getter

__all__ = [
    "OntobeeAligner",
    "get_ontobee",
]

DIRECTORY = Path(__file__).parent.resolve()
RAW_PATH = RAW_DIRECTORY / "ontobee.html"
PROCESSED_PATH = DIRECTORY / "processed.json"

URL = "http://www.ontobee.org/"
LEGEND = {
    "F": ["obofoundry", "ontology"],  # "Foundry",
    "L": ["obofoundry", "ontology"],  # "Library",
    "N": ["ontology"],  # "Not Specified/No",
}


def parse_ontobee(path: Path) -> dict[str, Record]:
    """Parse OntoBee."""
    with path.open() as f:
        soup = BeautifulSoup(f, "html.parser")

    ontology_list = soup.find(id="ontologyList")
    if ontology_list is None:
        raise ValueError
    table_body = ontology_list.find("tbody")
    if table_body is None:
        raise ValueError

    rv = {}
    for row in table_body.find_all("tr"):  # type:ignore
        cells = row.find_all("td")
        prefix = cells[1].text
        rv[prefix] = make_record(
            {
                "name": cells[2].text,
                "keywords": LEGEND[cells[3].text.upper()],
                # "link": cells[1].find("a").attrs["href"],
            }
        )
    return rv


get_ontobee = build_getter(
    processed_path=PROCESSED_PATH,
    raw_path=RAW_PATH,
    url=URL,
    func=parse_ontobee,
)


class OntobeeAligner(Aligner):
    """Aligner for OntoBee xref registry."""

    key = "ontobee"
    getter = get_ontobee
    curation_header: ClassVar[Sequence[str]] = ("name", "url")

    def get_curation_row(self, external_id: str, external_entry: dict[str, Any]) -> Sequence[str]:
        """Return the relevant fields from an OntoBee entry for pretty-printing."""
        return [
            textwrap.shorten(external_entry["name"] or "", 50),
            external_entry.get("uri_format") or "",
        ]


if __name__ == "__main__":
    OntobeeAligner.cli()
