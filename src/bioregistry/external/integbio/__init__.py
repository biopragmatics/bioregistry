"""Download the Integbio registry."""

from __future__ import annotations

import json
import logging
from collections.abc import Sequence
from pathlib import Path
from typing import Any, ClassVar

import pandas as pd
import requests
from bs4 import BeautifulSoup

from bioregistry.external.alignment_utils import Aligner

__all__ = [
    "IntegbioAligner",
    "get_integbio",
]

logger = logging.getLogger(__name__)

DIRECTORY = Path(__file__).parent.resolve()
PROCESSED_PATH = DIRECTORY / "processed.json"

SKIP = [
    "Link(s) to Downloadable data",
    "Link(s) to Metadata of downloadable data",
    "Link(s) to Terms of use",
    "Link(s) to How to use",
    "Link(s) to API / SPARQL endopoint",
    "Link to LSDB Archive",
    "Link to MEDALS Database list",
    "Link to TogoTV",
    "Similar databases",
    "Record maintainer",
    "Record source",
    "Acquisition date",
    "Organism(s) covered",
    "Date of creation of this record",
    "Last update date of this record",
    "Country/Region",
    "J-GLOBAL ID",  # about institutions?
    "Contact information of database",  # nice idea, but curation is bad so effectively unusable
]


def get_url() -> str:
    """Scrape the current download URL for Integbio.

    :returns: The URL of the Integbio data download.

    :raises ValueError: if the URL can't be found

    .. warning::

        Integbio deletes its old files, so it's impossible to download an old version of
        the database
    """
    base = "https://catalog.integbio.jp/dbcatalog/en/download"
    download_prefix = "/dbcatalog/files/zip/en_integbio_dbcatalog_ccbysa_"
    download_suffix = "_utf8.csv.zip"

    res = requests.get(base, timeout=15)
    soup = BeautifulSoup(res.text, "html.parser")
    for anchor in soup.find_all("a"):
        href: str | None = anchor.attrs["href"]
        if href is None:
            continue
        if href.startswith(download_prefix) and href.endswith(download_suffix):
            return "https://catalog.integbio.jp" + href
    raise ValueError(f"unable to find Integbio download link on {base}")


def _parse_references(s: str) -> list[str]:
    rv = []
    for part in s.strip().split("||"):
        ref = _parse_reference(part.strip())
        if ref:
            rv.append(ref)
    return rv


def _parse_reference(part: str) -> str | None:
    if "\\" in part:  # it's pubmed followed by equvalent DOI
        pubmed, _doi = part.split("\\")
        return pubmed
    if part.isnumeric():  # it's pubmed
        return part
    if part == "etc.":
        return None
    logger.debug(f"IntegBio unhandled reference part: {part}")
    return None


def _strip_split(s: str | None) -> list[str] | None:
    if pd.isna(s) or not s:
        return None
    return [k.strip() for k in s.strip().split("||")]


def _parse_fairsharing_url(s: str) -> str | None:
    if s.startswith("https://fairsharing.org/10.25504/"):
        return s.removeprefix("https://fairsharing.org/10.25504/")
    elif s.startswith("https://fairsharing.org/"):
        return s.removeprefix("https://fairsharing.org/")
    logger.debug(f"unhandled FAIRsharing: {s}")
    return None


def get_integbio(*, force_download: bool = False) -> dict[str, dict[str, Any]]:
    """Get the integbio resource."""
    url = get_url()
    df = pd.read_csv(url)
    df.rename(
        columns={
            "Database ID": "prefix",
            "Database name": "name",
            "Alternative name": "alt_name",
            "Database description": "description",
            "URL": "homepage",
            "Link to FAIRsharing": "fairsharing",
            "Reference(s) - PubMed ID/DOI": "references",
            "Language(s)": "languages",
            "Database maintenance site": "maintainer",
            "Tag - Target": "target_keywords",
            "Tag - Information type": "information_keywords",
            "Operational status": "status",
        },
        inplace=True,
    )
    for key in SKIP:
        del df[key]

    df["fairsharing"] = df["fairsharing"].map(_parse_fairsharing_url, na_action="ignore")
    df = df[df["languages"] != "ja"]  # skip only japanese language database for now
    del df["languages"]
    # df["languages"] = df["languages"].map(_strip_split, na_action="ignore")
    df["target_keywords"] = df["target_keywords"].map(_strip_split, na_action="ignore")
    df["information_keywords"] = df["information_keywords"].map(_strip_split, na_action="ignore")
    df["pubmeds"] = df["references"].map(_parse_references, na_action="ignore")
    df["description"] = df["description"].map(lambda s: s.replace("\r\n", "\n"), na_action="ignore")

    del df["references"]
    # TODO ground database maintenance with ROR?
    rv = {}
    for _, row in df.iterrows():
        rv[row["prefix"].lower()] = {k: v for k, v in row.items() if isinstance(v, (str, list))}
    PROCESSED_PATH.write_text(json.dumps(rv, indent=True, ensure_ascii=False, sort_keys=True))
    return rv


class IntegbioAligner(Aligner):
    """Aligner for the Integbio."""

    key = "integbio"
    alt_key_match = "name"
    getter = get_integbio
    curation_header: ClassVar[Sequence[str]] = ("name", "alt_name", "homepage")


if __name__ == "__main__":
    IntegbioAligner.cli()
