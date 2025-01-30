"""A script for semi-automatically importing part of Prefix Commons."""

import json

import click
import requests
from tqdm import tqdm

import bioregistry
from bioregistry import Resource, manager
from bioregistry.constants import BIOREGISTRY_MODULE
from bioregistry.external import get_prefixcommons
from bioregistry.schema_utils import add_resource

skip = {
    "pharmgkb",
    "pdb",
    "panther",
    "intenz",  # already mapped via "enzyme"
    "explorenz",  # already mapped via "enzyme"
    "geisha",  # resolution is broken
    "gopad",  # doesn't exist anymore
    "genomereviews",  # doesn't exist anymore
    "integr8",  # same as genome reviews, doesn't exist anymore
    "hdbase",  # doesn't exist anymore, silent redirect
    "mirortho",  # redirects to new site
    "hagr",  # nonsense
    "recode",  # dead
    "pathwayontology",  # duplicate of pw
    "pdbe",  # duplicate
}


def norm(s: str) -> str:
    """Normalize a string for dictionary key usage."""
    return s.lower().replace("-", "_").replace(" ", "")


@click.command()
def main():
    """Run semi-automated import of Prefix Commons."""
    dead_stuff_path = BIOREGISTRY_MODULE.join(name="pc_dead_prefixes.json")
    if dead_stuff_path.is_file():
        dead_prefixes = set(json.loads(dead_stuff_path.read_text()))
    else:
        dead_prefixes = set()
    click.echo(f"see {dead_stuff_path}")

    uniprot_pattern = bioregistry.get_resource("uniprot").get_pattern_re()
    pc = get_prefixcommons(force_download=False)
    prefixes = manager.get_registry_invmap("prefixcommons")
    c = 0
    for prefix, data in tqdm(pc.items(), unit="prefix", desc="Checking PC prefixes"):
        if prefix in prefixes or prefix in skip or prefix in dead_prefixes or len(prefix) < 4:
            continue
        if bioregistry.normalize_prefix(prefix):
            tqdm.write(f"[{prefix:15}] duplicate alignment")
            continue

        uri_format = data.get("uri_format")
        if uri_format is None:
            continue
        if not uri_format.endswith("$1"):
            tqdm.write(f"[{prefix:15}] URI format: {uri_format}")
            continue

        if not all(data.get(k) for k in ["name", "description", "homepage", "pattern", "example"]):
            continue

        example = data["example"]
        if uniprot_pattern.match(example):
            tqdm.write(f"[{prefix:15}] skipping duplicate of UniProt: {example}")
            continue

        example_url = uri_format.replace("$1", data["example"])

        tqdm.write(f"checking {prefix}")
        homepage_res = _works(data["homepage"])
        entry_res = _works(example_url)
        if homepage_res and entry_res:
            c += 1
            tqdm.write("adding " + click.style(prefix, fg="green"))
            add_resource(
                Resource(
                    prefix=norm(prefix),
                    mappings={"prefixcommons": prefix},
                    prefixcommons=data,
                )
            )
        else:
            dead_prefixes.add(prefix)
            dead_stuff_path.write_text(json.dumps(sorted(dead_prefixes), indent=2))

    click.echo(c)


def _works(url: str) -> bool:
    try:
        homepage_res = requests.head(url, timeout=3, allow_redirects=True)
    except OSError:
        return False
    else:
        return homepage_res.status_code == 200


if __name__ == "__main__":
    main()
