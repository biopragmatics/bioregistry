# -*- coding: utf-8 -*-

"""Download registry information from NCBI."""

import json
import logging
import re
from typing import Dict
from urllib.parse import urlsplit, urlunsplit

import click
from bs4 import BeautifulSoup
from pystow.utils import download

from bioregistry.data import EXTERNAL

__all__ = [
    "get_ncbi",
]

logger = logging.getLogger(__name__)

DIRECTORY = EXTERNAL / "ncbi"
DIRECTORY.mkdir(exist_ok=True, parents=True)
RAW_PATH = DIRECTORY / "raw.html"
PROCESSED_PATH = DIRECTORY / "processed.json"
URL = "https://www.ncbi.nlm.nih.gov/genbank/collab/db_xref/"
NCBI_URL_PARTS = urlsplit(URL)
DATA_TABLE_CAPTION_RE = re.compile(r"db_xref List")

MISSING = {
    "EnsemblGenomes-Gn",
}
REWRITES = {
    "JGI Phytozome": "Phytozome",
    "UniProtKB/Swiss-Prot": "UniProt",
}
XREF_PREFIX = [
    '/db_xref="',  # standard
    'db_xref="',  # ERIC
    '/dbxref="',  # PDB
    "/db_xref=",  # Xenbase
]
REDUNDANT = {
    "ATCC(dna)": "ATCC",
    "ATCC(in host)": "ATCC",
    "UniProtKB/TrEMBL": "UniProt",
    "LocusID": "GeneID",  # As of March 2005
}
OBSOLETE = {
    "ERIC",  # should be at http://www.ericbrc.org/portal/eric/, but gone.
    "PBmice",  # website down
}


def get_ncbi(force_download: bool = False) -> Dict[str, Dict[str, str]]:
    """Get the NCBI data."""
    if PROCESSED_PATH.exists() and not force_download:
        with PROCESSED_PATH.open() as file:
            return json.load(file)

    download(url=URL, path=RAW_PATH, force=True)
    with RAW_PATH.open() as file:
        soup = BeautifulSoup(file, "html.parser")
    # find the data table based on its caption element
    data_table = soup.find("caption", string=DATA_TABLE_CAPTION_RE).parent

    rv = {}
    for row in data_table.find_all("tr"):
        cells = row.find_all("td")
        if not cells:
            continue

        prefix = cells[0].text.strip()
        prefix = REWRITES.get(prefix, prefix)

        if prefix in REDUNDANT:
            logger.warning(f"skipping {prefix}")
            continue

        name = cells[2].text.strip()
        if not (prefix and name):  # blank line
            continue

        item = {"name": name}

        link = cells[0].find("a")
        if link and "href" in link.attrs:
            link_href = link.attrs["href"].strip()
            if link_href:
                url_parts = urlsplit(link_href)
                if not url_parts.netloc:  # handle relative links
                    if url_parts.path.startswith("/"):  # relative to site root
                        url_parts = (
                            NCBI_URL_PARTS.scheme,
                            NCBI_URL_PARTS.netloc,
                            url_parts.path,
                            url_parts.query,
                            url_parts.fragment,
                        )
                    else:  # relative to the page we got it from
                        url_parts = (
                            NCBI_URL_PARTS.scheme,
                            NCBI_URL_PARTS.netloc,
                            NCBI_URL_PARTS.path + url_parts.path,
                            url_parts.query,
                            url_parts.fragment,
                        )
                    item["homepage"] = urlunsplit(url_parts)
                else:  # absolute links can pass through unchanged
                    item["homepage"] = link_href

        if prefix not in MISSING:
            examples = cells[4].text.strip()
            # only bother with the first line of examples
            example = examples.split("\n")[0].strip()

            for xref_prefix in XREF_PREFIX:
                if example.startswith(xref_prefix):
                    stripped_example = example[len(xref_prefix) :].rstrip('"').lstrip()
                    break
            else:
                raise ValueError(f"[{prefix}] wrong xref prefix: {example}")

            if ":" not in stripped_example:
                raise ValueError(f"[{prefix}] not formatted as CURIE: {example}")

            if not stripped_example.lower().startswith(prefix.lower()):
                raise ValueError(f"[{prefix}] invalid prefix: {example}")

            parsed_prefix, identifier = [x.strip() for x in stripped_example.split(":", 1)]
            if prefix.casefold() != REWRITES.get(parsed_prefix, parsed_prefix).casefold():
                raise ValueError(
                    f"example does not start with prefix {prefix} -> {identifier} from {example}"
                )

            item["example"] = identifier

        rv[prefix] = item

    with PROCESSED_PATH.open("w") as file:
        json.dump(rv, file, indent=2, sort_keys=True)

    return rv


@click.command()
def main():
    """Reload NCBI data."""
    r = get_ncbi(force_download=True)
    click.echo(f"Got {len(r)} records")


if __name__ == "__main__":
    main()
