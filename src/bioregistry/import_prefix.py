import json

import bioregistry
from bioregistry import manager, Resource
from bioregistry.external import get_prefixcommons
from bioregistry.schema_utils import add_resource
import requests
from tqdm import tqdm
import click
from bioregistry.constants import BIOREGISTRY_MODULE

skip = {
    "pharmgkb",
    "pdb",
    "panther",
}

def norm(s: str) -> str:
    """Normalize a string for dictionary key usage."""
    return s.lower().replace("-", "_").replace(" ", "")

@click.command()
def main():
    dead_stuff_path = BIOREGISTRY_MODULE.join(name="pc_dead_prefixes.json")
    if dead_stuff_path.is_file():
        dead_prefixes = set(json.load(dead_stuff_path.read_text()))
    else:
        dead_prefixes = set()
    print(f"see {dead_stuff_path}")

    uniprot_pattern = bioregistry.get_resource("uniprot").get_pattern_re()
    pc = get_prefixcommons(force_download=False)
    prefixes = manager.get_registry_invmap("prefixcommons")
    c = 0
    for prefix, data in tqdm(pc.items(), unit="prefix", desc="Checking PC prefixes"):
        if prefix in prefixes or prefix in skip:
            continue
        if bioregistry.normalize_prefix(prefix):
            tqdm.write(f"duplicate alignment to prefixcommons:{prefix}")
            continue
        if not all(
            data.get(k)
            for k in ["name", "description", "homepage", "pattern", "example", "uri_format"]
        ):
            continue

        example = data["example"]
        if uniprot_pattern.match(example):
            continue
        uri_format = data['uri_format']
        if not uri_format.endswith("$1"):
            continue

        pubmeds = data.get("pubmed_ids")
        if not pubmeds:
            continue

        example_url = data["uri_format"].replace("$1", data["example"])

        tqdm.write(f"checking {prefix}")
        homepage_res = _works(data["homepage"])
        entry_res = _works(example_url)
        if homepage_res and entry_res:
            c += 1
            tqdm.write("adding " + click.style(prefix, fg="green"))
            add_resource(Resource(
                prefix=norm(prefix),
                mappings=dict(prefixcommons=prefix),
                prefixcommons=data,
            ))
        else:
            dead_prefixes.add(prefix)
            dead_stuff_path.write_text(json.dumps(sorted(dead_prefixes), indent=2))

    print(c)


def _works(url: str) -> bool:
    try:
        homepage_res = requests.head(url, timeout=3, allow_redirects=True)
    except IOError:
        return False
    else:
        return homepage_res.status_code == 200


if __name__ == '__main__':
    main()
