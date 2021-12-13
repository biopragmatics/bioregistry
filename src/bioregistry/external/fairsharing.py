# -*- coding: utf-8 -*-

"""Scraper for FAIRsharing.

.. seealso:: https://beta.fairsharing.org/API_doc
"""

import json
import requests
from tqdm import tqdm
from typing import Optional

import pystow
from bioregistry.data import EXTERNAL

DIRECTORY = EXTERNAL / "miriam"
DIRECTORY.mkdir(exist_ok=True, parents=True)
RAW_PATH = DIRECTORY / "raw.json"
PROCESSED_PATH = DIRECTORY / "processed.json"
MIRIAM_URL = "https://registry.api.identifiers.org/resolutionApi/getResolverDataset"

BASE_URL = "https://api.fairsharing.org"
SIGNIN_URL = f"{BASE_URL}/users/sign_in"
RECORDS_URL = f"{BASE_URL}/fairsharing_records"


def get_fairsharing(force_download: bool = False):
    """Get the FAIRsharing registry."""
    if PROCESSED_PATH.exists() and not force_download:
        with PROCESSED_PATH.open() as file:
            return json.load(file)

    client = FairsharingClient()
    rv = list(tqdm(client.iter_records(), unit_scale=True, unit="record", desc="Downloading FAIRsharing"))

    with PROCESSED_PATH.open("w") as file:
        json.dump(rv, file, indent=2, sort_keys=True)
    return rv


class FairsharingClient:
    def __init__(self, user: Optional[str] = None, password: Optional[str] = None):
        self.username = pystow.get_config(
            "fairsharing", "login", passthrough=user, raise_on_missing=True
        )
        self.password = pystow.get_config(
            "fairsharing", "password", passthrough=password, raise_on_missing=True
        )
        self.jwt = self.get_jwt()
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Accept": "application/json",
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.jwt}",
            }
        )

    def get_jwt(self) -> str:
        """Get the JWT."""
        payload = {
            "user": {
                "login": self.username,
                "password": self.password,
            },
        }
        res = requests.post(SIGNIN_URL, json=payload).json()
        return res["jwt"]

    def get(self, *args, **kwargs) -> requests.Response:
        return self.session.get(*args, **kwargs)

    def iter_records(self):
        yield from self._iter_records_helper(RECORDS_URL)

    def _iter_records_helper(self, url: str):
        res = self.get(url).json()
        yield from res["data"]
        next_url = res["links"].get("next")
        if next_url:
            yield from self._iter_records_helper(next_url)


if __name__ == "__main__":
    get_fairsharing(force_download=True)
