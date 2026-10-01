"""Add PyOBO ontology artifacts from https://github.com/biopragmatics/obo-db-ingest."""

import requests
import yaml
from tqdm import tqdm

from bioregistry import manager


def main() -> None:
    """Add ontology artifacts."""
    manifest_url = (
        "https://github.com/biopragmatics/obo-db-ingest/raw/refs/heads/main/docs/_data/manifest.yml"
    )
    response = requests.get(manifest_url, timeout=10)
    response.raise_for_status()
    manifest = yaml.safe_load(response.text)

    for prefix, data in tqdm(manifest["resources"].items()):
        resource = manager.registry[prefix]

        obo = data.get("obo")
        if obo:
            resource.download_obo = obo["iri"]

        owl = data.get("owl")
        if owl:
            resource.download_owl = owl["iri"]

        obograph = data.get("obograph")
        if obograph:
            resource.download_json = obograph["iri"]

        # can also get `ofn`

    manager.write_registry()


if __name__ == "__main__":
    main()
