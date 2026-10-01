"""A script for renaming a metaprefix in the Bioregistry."""

import json

import click

from bioregistry.constants import BIOREGISTRY_PATH, CURATED_MAPPINGS_PATH, METAREGISTRY_PATH


@click.command()
@click.argument("old_metaprefix")
@click.argument("new_metaprefix")
def main(old_metaprefix: str, new_metaprefix: str) -> None:
    """Rename a metaprefix."""
    registry = json.loads(BIOREGISTRY_PATH.read_text())
    for value in registry.values():
        if old_metaprefix in value:
            value[new_metaprefix] = value.pop(old_metaprefix)
        mappings = value.get("mappings")
        if mappings and old_metaprefix in mappings:
            mappings[new_metaprefix] = mappings.pop(old_metaprefix)
    BIOREGISTRY_PATH.write_text(json.dumps(registry, indent=2, ensure_ascii=False) + "\n")

    metaregistry = json.loads(METAREGISTRY_PATH.read_text())
    for record in metaregistry["metaregistry"]:
        if record["prefix"] == old_metaprefix:
            record["prefix"] = new_metaprefix
    METAREGISTRY_PATH.write_text(json.dumps(metaregistry, indent=2, ensure_ascii=False) + "\n")

    # Rewrite SSSOM without loading it through sssom-pydantic
    sssom_raw_text = CURATED_MAPPINGS_PATH.read_text()
    sssom_raw_text = sssom_raw_text.replace(f"{old_metaprefix}:", f"{new_metaprefix}:")
    CURATED_MAPPINGS_PATH.write_text(sssom_raw_text)


if __name__ == "__main__":
    main()
