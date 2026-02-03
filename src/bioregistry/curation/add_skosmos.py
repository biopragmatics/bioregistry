"""This script adds skosmos."""

import json
import sys
from typing import Any

import click
import requests
import skosmos_client
from tabulate import tabulate
from tqdm import tqdm

import bioregistry

SKOSMOS_APIS: list[tuple[str, str | None]] = [
    ("finto", "https://api.finto.fi/rest/v1/"),
    # see https://vocabs-api.acdh.oeaw.ac.at, this is the same as DARIAH
    ("acdhchvs", "https://vocabs.acdh.oeaw.ac.at/rest/v1/"),
    ("loterre", "https://skosmos.loterre.fr/rest/v1/"),
    # see https://bartoc.org/en/node/18937
    ("legilux", "https://data.legilux.public.lu/vocabulaires/rest/v1/"),
    ("gesis", None),
    ("lincs.skosmos", None),
    ("zpid", "https://vocabs.leibniz-psychology.org/rest/v1/"),
    ("zbw", None),
    ("sshopencloud", "http://vocabs.acdh.oeaw.ac.at/rest/v1/"),
    ("nbvok", "https://www.nb.no/nbvok/rest/v1/"),
    ("ilc4clarin", None)
]

BARTOC_REGISTRIES_URL = "https://bartoc.org/registries"
SKIP = {
    "18943",  # BARTOC Skosmos
}


def get_bartoc_skosmos() -> list[tuple[str, str | None, dict[str, Any]]]:
    """Get BARTOC registries with SKOSMOS APIs."""
    res = requests.get(BARTOC_REGISTRIES_URL, timeout=5, params={"format": "jskos"})
    res_json = res.json()
    rows = []
    for key, data in res_json.items():
        prefix = key.removeprefix("http://bartoc.org/en/node/")
        if prefix in SKIP:
            continue
        for api in data.get("API", []):
            if api["type"] == "http://bartoc.org/api-type/skosmos":
                api_url = api["url"] + "rest/v1/"
                break
        else:
            # if we didn't find a SKOSMOS API endpoint, skip this record
            continue

        rows.append((prefix, api_url, data))
    return rows


@click.command()
def main() -> None:
    """Import content from skosmos."""
    yy = bioregistry.get_registry_invmap("bartoc")
    xx = get_bartoc_skosmos()
    srows = [
        (prefix, data["prefLabel"]["en"], data["url"].rstrip("/"))
        for prefix, url, data in xx
        if prefix not in yy
    ]
    if srows:
        click.echo("\nStill need to curate prefixes (or skips) for the following SKOSMOS listed in BARTOC:\n")
        click.echo(tabulate(srows, headers=["bartoc", "name", "homepage"]))
        raise sys.exit(0)

    lang = "en"

    rows = []

    for service_prefix, api_base in SKOSMOS_APIS:
        if not api_base:
            continue
        service_name = bioregistry.get_name(service_prefix, strict=True)
        client = skosmos_client.SkosmosClient(api_base)
        for v in tqdm(client.vocabularies(lang), desc=service_name, unit="vocabulary"):
            if v["id"] != v["uri"]:
                raise ValueError(f"different URI/ID for {v}")

            prefix = v["id"]
            name = v["title"]

            # strip off redundant prefix
            pfx = prefix + " - "
            if name.lower().startswith(pfx):
                name = name[len(pfx) :]

            v = client.get_vocabulary(prefix, lang=lang)
            tqdm.write(json.dumps(v))
            # v["@context"]["@base"]
            language = v["defaultLanguage"]
            concept_schemes = v["conceptschemes"]
            if not concept_schemes:
                raise
            elif len(concept_schemes) == 1:
                concept_scheme = concept_schemes[0]
            else:
                # click.echo(f"[{name}] conflicting concept schemes for {prefix}")
                concept_scheme = concept_schemes[0]

            uri_prefix = concept_scheme["uri"]
            uri_format = uri_prefix + "$1"

            types = [t["prefLabel"] for t in v.get("type", [])]

            req = requests.get(f"{client.api_base}{prefix}/index/", timeout=5)
            req.raise_for_status()
            res_json = req.json()
            letter = res_json["indexLetters"][0]

            req2 = requests.get(f"{client.api_base}{prefix}/index/{letter}", timeout=5)
            req2.raise_for_status()
            res2_json = req2.json()
            index_concepts = res2_json["indexConcepts"]
            if index_concepts:
                example_luid = index_concepts[0]["localname"]
            else:
                example_luid = None

            # TODO get TTL, parse with RDFLib, query for x a skos:ConceptScheme
            #  and parse out more metadata like description and license

            rows.append((service_prefix, prefix, name, language, uri_prefix, example_luid, types))

            bioregistry.Resource(
                prefix=prefix,
                name=name,
                uri_format=uri_format,
                example=example_luid,
                homepage=uri_prefix,
            )

    click.echo(tabulate(rows))


if __name__ == "__main__":
    main()
