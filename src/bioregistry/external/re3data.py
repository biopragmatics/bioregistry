# -*- coding: utf-8 -*-

"""Re3data is a registry of research data repositories.

API documentation is available at https://www.re3data.org/api/doc
Michael Witt (mwitt@purdue.edu, orcid:0000-0003-4221-7956)
"""

import json
from xml.etree import ElementTree

import requests
from tqdm.auto import tqdm

from bioregistry.constants import EXTERNAL
from bioregistry.utils import removeprefix

__all__ = [
    "get_re3data",
]

DIRECTORY = EXTERNAL / "re3data"
DIRECTORY.mkdir(exist_ok=True, parents=True)
RAW_PATH = DIRECTORY / "raw.json"
PROCESSED_PATH = DIRECTORY / "processed.json"

BASE_URL = "https://www.re3data.org"
SCHEMA = "{http://www.re3data.org/schema/2-2}"


def get_re3data(force_download: bool = False):
    """Get the re3data registry.

    This takes about 9 minutes since it has to look up each of the ~3K
    records with their own API call.

    :param force_download: If true, re-downloads the data
    :returns: The re3data pre-processed data
    """
    if PROCESSED_PATH.exists() and not force_download:
        with PROCESSED_PATH.open() as file:
            return json.load(file)

    res = requests.get(BASE_URL + "/api/v1/repositories")
    records = {}

    tree = ElementTree.fromstring(res.text)
    repositories = list(tree.findall("repository"))

    for repository in tqdm(repositories, unit_scale=True):
        link = repository.find("link").attrib["href"]
        res_inner = requests.get(BASE_URL + link)
        tree_inner = ElementTree.fromstring(res_inner.text)[0]
        identifier = repository.find("id").text
        data = {
            "prefix": identifier,
            "name": repository.find("name").text,
            "description": tree_inner.find(f"{SCHEMA}description").text,
            "homepage": tree_inner.find(f"{SCHEMA}repositoryURL").text,
        }

        doi_element = repository.find("doi")
        if doi_element:
            data["doi"] = removeprefix(doi_element.text, "https://doi.org/")

        license_element = tree_inner.find(f"{SCHEMA}databaseLicense/{SCHEMA}databaseLicenseName")
        if license_element:
            data["license"] = license_element.text

        xref_element = tree_inner.find(f"{SCHEMA}repositoryIdentifier")
        if xref_element:
            data["xref"] = xref_element.text

        records[identifier] = {k: v.strip() for k, v in data.items()}

    with PROCESSED_PATH.open("w") as file:
        json.dump(records, file, indent=2, sort_keys=True, ensure_ascii=False)

    return records


if __name__ == "__main__":
    get_re3data(force_download=True)
