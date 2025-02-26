"""Download registry information from Pathguide."""

import requests
from bs4 import BeautifulSoup

from bioregistry.external.alignment_utils import Aligner

__all__ = [
    "PathguideAligner",
    "get_pathguide",
]


def get_pathguide(*, force_download: bool = False):
    """Get the Pathguide metdata."""
    res = requests.get("http://pathguide.org/")
    soup = BeautifulSoup(res.text, "html.parser")
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
        rv[pathguide_id] = {
            "prefix": pathguide_id,
            "abbreviation": abbreviation,
            "name": name,
            "homepage": homepage,
        }
        if standards:
            rv[pathguide_id]["keywords"] = standards
    return rv


class PathguideAligner(Aligner):
    """Aligner for the Pathguide."""

    key = "pathguide"
    alt_key_match = "abbreviation"
    getter = get_pathguide
    curation_header = ("abbreviation", "name", "homepage")


if __name__ == "__main__":
    PathguideAligner.cli()
