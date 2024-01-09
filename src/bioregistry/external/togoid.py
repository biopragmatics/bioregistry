# -*- coding: utf-8 -*-

"""Download TogoID."""

import yaml
import json

import requests

from bioregistry.constants import EXTERNAL, URI_FORMAT_KEY

__all__ = [
    "get_togoid",
]

DIRECTORY = EXTERNAL / "togoid"
DIRECTORY.mkdir(exist_ok=True, parents=True)
RAW_PATH = DIRECTORY / "raw.json"
PROCESSED_PATH = DIRECTORY / "processed.json"
URL = (
    "https://raw.githubusercontent.com/togoid/togoid-converter/develop/swagger/swagger-config.yaml"
)


def get_togoid(*, force_refresh: bool = False):
    """Get the TogoID data."""
    if PROCESSED_PATH.exists() and not force_refresh:
        with PROCESSED_PATH.open() as file:
            return json.load(file)
    rv = {}
    data = yaml.safe_load(requests.get(URL).text)
    subdata = data["paths"]["/config/dataset"]["get"]["responses"][200]["schema"]["properties"]
    for prefix, record in subdata.items():
        dd = {k: v["example"] for k, v in record["properties"].items() if "example" in v}
        rr = {
            "prefix": prefix,
            "name": dd["label"],
            "pattern": dd["regex"].replace("<id>", ""),
            URI_FORMAT_KEY: dd["prefix"] + "$1",  # this is right, they named it weird
        }
        examples_lists = dd.get("examples", [])
        if examples_lists:
            rr["examples"] = examples_lists[0]
        category = dd.get("category")
        if category:
            rr["keywords"] = [category]
        rv[prefix] = rr
    with PROCESSED_PATH.open("w") as file:
        json.dump(rv, file, indent=2, sort_keys=True)
    return rv


if __name__ == "__main__":
    get_togoid(force_refresh=True)
