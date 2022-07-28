# -*- coding: utf-8 -*-

"""Re3data is a registry of research data repositories.

API documentation is available at https://www.re3data.org/api/doc
Michael Witt (mwitt@purdue.edu, orcid:0000-0003-4221-7956)
"""

import requests
from xml.etree import ElementTree
from bioregistry.utils import removeprefix
from tqdm.auto import tqdm

__all__ = [
    "get_re3data",
]

BASE_URL = "https://www.re3data.org"
SCHEMA = "{http://www.re3data.org/schema/2-2}"


def get_re3data():
    """Get the re3data registry.

    This takes about 9 minutes since it has to look up each of the ~3K
    records with their own API call.

    :returns: A
    """
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

        records[identifier] = data

    return records


if __name__ == '__main__':
    get_re3data()
