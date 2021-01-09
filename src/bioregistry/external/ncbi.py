# -*- coding: utf-8 -*-

"""Download registry information from NCBI."""

import re
from typing import Dict, Optional

import click
import pystow
from bs4 import BeautifulSoup

from ..constants import BIOREGISTRY_MODULE

URL = "https://www.ncbi.nlm.nih.gov/genbank/collab/db_xref/"
DATA_TABLE_CAPTION_RE = re.compile(r"db_xref List")


def get_ncbi() -> Dict[str, str]:
    """Get the NCBI data."""
    path = BIOREGISTRY_MODULE.ensure(url=URL)
    with open(path) as f:
        soup = BeautifulSoup(f, "html.parser")
    # find the data table based on its caption element
    data_table = soup.find("caption", string=DATA_TABLE_CAPTION_RE).parent

    rv = {}
    for row in data_table.find_all("tr"):
        cells = row.find_all("td")
        if not cells:
            continue
        prefix = cells[0].text.strip()
        provider = cells[2].text.strip()
        if not (prefix and provider):
            continue

        rv[prefix] = provider

    return rv


@click.command()
def main():
    """Reload NCBI data."""
    get_ncbi()


if __name__ == "__main__":
    main()
