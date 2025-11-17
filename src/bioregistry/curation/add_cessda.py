"""Add content from CESSDA.

Docs on https://api.tech.cessda.eu/
"""

import json
import textwrap

import click
import pystow
import requests
from tabulate import tabulate
from tqdm import tqdm

import bioregistry
from bioregistry.schema.struct import Organization

BASE = "https://vocabularies.cessda.eu"
MODULE = pystow.module("cessda")

AGENCIES: dict[str, Organization] = {
    "GESIS": Organization(
        ror="018afyw53", name="GESIS - Leibniz-Institute for the Social Sciences"
    ),
    "DDI Alliance": Organization(ror="015em2733", name="Data Documentation Initiative Alliance"),
    "CESSDA": Organization(
        ror="02wg9xc72", name="Consortium of European Social Science Data Archives"
    ),
}
NN = {"GESIS": "gesis", "DDI Alliance": "ddi", "CESSDA": "cessda"}
LICENSES = {
    "http://creativecommons.org/licenses/by/4.0/": "CC-BY-4.0",
}


@click.command()
def main() -> None:
    """Add CESSDA prefixes."""
    res_json = MODULE.ensure_json(url=f"{BASE}/v2/vocabularies-published", name="index.json")

    rows = []
    for agency, superdata in res_json.items():
        for subprefix, language_to_version_to_url in tqdm(superdata.items(), desc=agency):
            path = MODULE.join(name=f"{subprefix}.json")
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
                    tqdm.write(
                        f"[{subprefix}] no english, choose from {set(language_to_version_to_url)}"
                    )
                    continue

                res_inner = requests.get(f"{BASE}{url_last}", timeout=10)
                res_inner.raise_for_status()
                data = res_inner.json()
                path.write_text(json.dumps(data, indent=2))

            name = data.get("titleEn") or data.get("titleAll")
            description = data.get("definitionEn")
            version = data.get("versionEn")

            version_dict = data["versions"][0]
            notation = version_dict["notation"]  # also same as prefix

            concept = version_dict["concepts"][0]
            example = concept["notation"]

            # uri format
            uri_format = f"https://vocabularies.cessda.eu/vocabulary/{notation}?lang=en#code_$1"

            prefix = f"{NN[agency]}.{notation.lower()}"
            resource = bioregistry.Resource(
                prefix=prefix,
                name=name,
                example=example,
                description=description,
                license=LICENSES[version_dict["licenseLink"]],
                version=version,
                uri_format=uri_format,
                owners=[AGENCIES[agency]],
            )
            #bioregistry.add_resource(resource)
            #bioregistry.manager.write_registry()

            rows.append(
                (
                    agency,
                    notation,
                    name,
                    example,
                    textwrap.shorten(description, 60),
                    version,
                    license,
                    uri_format,
                )
            )

    click.echo(tabulate(rows))


if __name__ == "__main__":
    main()
