# -*- coding: utf-8 -*-

"""Download the NCBO BioPortal registry.

Get an API key by logging up, signing in, and navigating to https://bioportal.bioontology.org/account.
"""

import json

import pystow
import requests
from tqdm.contrib.concurrent import thread_map

from bioregistry.constants import EXTERNAL

__all__ = [
    "get_bioportal",
]

DIRECTORY = EXTERNAL / "bioportal"
DIRECTORY.mkdir(exist_ok=True, parents=True)
RAW_PATH = DIRECTORY / "raw.json"
PROCESSED_PATH = DIRECTORY / "processed.json"
BIOPORTAL_API_KEY = pystow.get_config("bioportal", "api_key")
BASE_URL = "https://data.bioontology.org"


def query(url: str, **params) -> requests.Response:
    """Query the given endpoint on BioPortal.

    :param url: URL to query
    :param params: Kwargs to give as params to :func:`requests.get`
    :returns: The response from :func:`requests.get`
    :raises ValueError: if there's no API key for bioportal

    The rate limit is 15 queries per second. See:
    https://www.bioontology.org/wiki/Annotator_Optimizing_and_Troublehooting
    """
    if BIOPORTAL_API_KEY is None:
        raise ValueError("missing API key for bioportal")
    params.setdefault("apikey", BIOPORTAL_API_KEY)
    return requests.get(url, params=params)


def get_bioportal(force_download: bool = False):
    """Get the BioPortal registry."""
    if PROCESSED_PATH.exists() and not force_download:
        with PROCESSED_PATH.open() as file:
            return json.load(file)

    # see https://data.bioontology.org/documentation#Ontology
    res = query(BASE_URL + "/ontologies", summaryOnly=False, notes=True)
    records = res.json()
    with RAW_PATH.open("w") as file:
        json.dump(records, file, indent=2, sort_keys=True)

    records = thread_map(_process, records, disable=True)
    rv = {result["prefix"]: result for result in records}

    with PROCESSED_PATH.open("w") as file:
        json.dump(rv, file, indent=2, sort_keys=True)
    return rv


def _process(entry):
    bioportal_key = entry["acronym"]
    extra_data = {}
    # res = query(f'{BASE_URL}/ontologies/{bioportal_key}/latest_submission')
    # if res:
    #     extra_data = res.json()
    # else:
    #     print('failed on', bioportal_key)
    #     extra_data = {}

    contact = (extra_data.get("contact") or [{}])[0]
    rv = {
        "prefix": bioportal_key,
        "name": entry["name"],
        "description": extra_data.get("description"),
        "contact": contact.get("email"),
        "contact.label": contact.get("name"),
        "homepage": extra_data.get("homepage"),
        "version": extra_data.get("version"),
        "publication": extra_data.get("publication"),
    }
    return {k: v for k, v in rv.items() if v is not None}


if __name__ == "__main__":
    print(len(get_bioportal(force_download=True)))  # noqa:T201
