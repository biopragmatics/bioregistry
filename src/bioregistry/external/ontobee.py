# -*- coding: utf-8 -*-

"""Download registry information from OntoBee."""

import json

from bs4 import BeautifulSoup
from pystow.utils import download

from bioregistry.constants import EXTERNAL

DIRECTORY = EXTERNAL / "ontobee"
DIRECTORY.mkdir(exist_ok=True, parents=True)
RAW_PATH = DIRECTORY / "raw.html"
PROCESSED_PATH = DIRECTORY / "processed.json"

URL = "http://www.ontobee.org/"
LEGEND = {
    "F": "Foundry",
    "L": "Library",
    "N": "Not Specified/No",
}


def get_ontobee(force_download: bool = False):
    """Get the OntoBee registry."""
    if PROCESSED_PATH.exists() and not force_download:
        with PROCESSED_PATH.open() as file:
            return json.load(file)

    download(url=URL, path=RAW_PATH, force=True)
    with RAW_PATH.open() as f:
        soup = BeautifulSoup(f, "html.parser")

    rv = {}
    for row in soup.find(id="ontologyList").find("tbody").find_all("tr"):
        cells = row.find_all("td")
        prefix = cells[1].text
        rv[prefix] = {
            "name": cells[2].text,
            "library": LEGEND[cells[3].text.upper()],
            # "link": cells[1].find("a").attrs["href"],
        }

    with PROCESSED_PATH.open("w") as file:
        json.dump(rv, file, indent=2, sort_keys=True)

    return rv


if __name__ == "__main__":
    get_ontobee()
