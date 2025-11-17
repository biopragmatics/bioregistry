"""Add content from CESSDA.

Docs on https://api.tech.cessda.eu/
"""

import json
from typing import Any

import requests
from tqdm import tqdm
from tabulate import tabulate
import click
import bioregistry
import pystow

BASE = "https://vocabularies.cessda.eu"
MODULE = pystow.module("cessda")


def main() -> None:
    res_json = MODULE.ensure_json(url=f"{BASE}/v2/vocabularies-published", name="index.json")

    rows = []
    for superkey, superdata in res_json.items():
        for prefix, language_to_version_to_url in tqdm(superdata.items(), desc=superkey):
            path = MODULE.join(name=f"{prefix}.json")
            if path.is_file():
                data = json.loads(path.read_text())
            else:
                if "en(SL)" in language_to_version_to_url:
                    v = language_to_version_to_url["en(SL)"]
                    version, url_last = max(v.items())
                # elif "en(TL)" in language_to_version_to_url:
                #     v = language_to_version_to_url["en(TL)"]
                #     version, url_last = max(v.items())
                else:
                    tqdm.write(f"[{prefix}] no english, choose from {set(language_to_version_to_url)}")
                    continue
                res_inner = requests.get(f"{BASE}{url_last}", timeout=10)
                res_inner.raise_for_status()
                data = res_inner.json()
                path.write_text(json.dumps(data, indent=2))

            name = data.get("titleEn") or data.get("titleAll")
            description = data.get("definitionEn")
            version = data.get("versionEn")

            version_dict = data['versions'][0]
            license = version_dict.get('licenseLink')
            notation = version_dict['notation']  # also same as prefix

            concept = version_dict['concepts'][0]
            example = concept['notation']

            # uri format
            uri_format = f"https://vocabularies.cessda.eu/vocabulary/{notation}?lang=en#code_$1"

            resource = bioregistry.Resource(
                prefix=notation,
                name=name,
                example=example,
                description=description,
                license=license,
                version=version,
                uri_format=uri_format,
            )
            
            rows.append((superkey, notation, name, example, description, version, license, uri_format))

    click.echo(tabulate(rows))


if __name__ == '__main__':
    main()
