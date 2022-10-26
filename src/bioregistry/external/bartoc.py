import requests
import json
from bioregistry.license_standardizer import standardize_license
from bioregistry.constants import EXTERNAL

DIRECTORY = EXTERNAL / "bartoc"
DIRECTORY.mkdir(exist_ok=True, parents=True)
PROCESSED_PATH = DIRECTORY / "processed.json"
URL = "https://bartoc.org/data/dumps/latest.ndjson"


def get_bartoc(force: bool = False)
    if PROCESSED_PATH.is_file() and not force:
        return json.loads(PROCESSED_PATH.read_text())
    rv = {}
    for line in requests.get(URL).iter_lines():
        record = json.loads(line)
        record = process_record(record)
        rv[record["prefix"]] = rv

    PROCESSED_PATH.write_text(json.dumps(rv, indent=2, ensure_ascii=True, sort_keys=True))
    return rv


def process_record(record):
    rv = {
        "prefix": record["uri"][len("http://bartoc.org/en/node/"):],
        "description": record.get("definition", {}).get("en")
        "homepage": record.get("url"),
        "name": record.get("prefLabel", {}).get("en"),
        "pattern": record.get("notationPattern"),
    }
    for license in record.get("license", []):
        license_key = standardize_license(license["uri"])
        if license_key:
            rv["license"] = license_key

    return {k: v for k, v in rv.items() if k and v}


if __name__ == '__main__':
    get_bartoc()
