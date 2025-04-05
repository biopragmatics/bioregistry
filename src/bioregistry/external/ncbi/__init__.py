"""Download registry information from NCBI."""

import json
import logging
import re
import textwrap
from collections.abc import Sequence
from pathlib import Path
from typing import Any, ClassVar
from urllib.parse import urlsplit, urlunsplit

from bs4 import BeautifulSoup
from pystow.utils import download

from bioregistry.constants import RAW_DIRECTORY
from bioregistry.external.alignment_utils import Aligner, load_processed

__all__ = [
    "NcbiAligner",
    "get_ncbi",
]

logger = logging.getLogger(__name__)

DIRECTORY = Path(__file__).parent.resolve()
RAW_PATH = RAW_DIRECTORY / "ncbi.html"
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


def get_ncbi(force_download: bool = False) -> dict[str, dict[str, str]]:
    """Get the NCBI data."""
    if PROCESSED_PATH.exists() and not force_download:
        return load_processed(PROCESSED_PATH)

    download(url=URL, path=RAW_PATH, force=True)
    with RAW_PATH.open() as file:
        soup = BeautifulSoup(file, "html.parser")
    # find the data table based on its caption element
    data_table_child = soup.find("caption", string=DATA_TABLE_CAPTION_RE)
    if data_table_child is None:
        raise ValueError

    data_table = data_table_child.parent
    if data_table is None:
        raise ValueError

    rv = {}
    for row in data_table.find_all("tr"):
        cells = row.find_all("td")
        if not cells:
            continue

        prefix = cells[0].text.strip()
        prefix = REWRITES.get(prefix, prefix)

        if prefix in REDUNDANT:
            logger.debug(f"skipping {prefix}")
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


class NcbiAligner(Aligner):
    """Aligner for NCBI xref registry."""

    key = "ncbi"
    getter = get_ncbi
    getter_kwargs: ClassVar[dict[str, Any]] = {"force_download": False}
    curation_header: ClassVar[Sequence[str]] = ("name", "example", "homepage")

    def get_curation_row(self, external_id: str, external_entry: dict[str, Any]) -> Sequence[str]:
        """Return the relevant fields from an NCBI entry for pretty-printing."""
        return [
            textwrap.shorten(external_entry["name"], 50),
            external_entry.get("example", ""),
            external_entry.get("homepage", ""),
        ]


if __name__ == "__main__":
    NcbiAligner.cli()
