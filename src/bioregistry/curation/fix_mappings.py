"""Remove mappings that have been manually curated as false."""

import json

import click
import curies
from pystow.utils import safe_open_dict_reader

from bioregistry.constants import BIOREGISTRY_PATH, CURATED_MAPPINGS_PATH


@click.command()
def main() -> None:
    """Remove mappings that have been manually curated as false."""
    registry = json.loads(BIOREGISTRY_PATH.read_text())
    with safe_open_dict_reader(CURATED_MAPPINGS_PATH) as reader:
        for record in reader:
            if record["predicate_modifier"] != "Not":
                continue
            prefix = record["subject_id"].removeprefix("bioregistry:")
            metaprefix, value = curies.ReferenceTuple.from_curie(record["object_id"])
            mappings = registry[prefix].get("mappings")
            if not mappings:
                continue
            if mappings.get(metaprefix) == value:
                del registry[prefix][metaprefix]
                del registry[prefix]["mappings"][metaprefix]

    for v in registry.values():
        if "mappings" in v and not v["mappings"]:
            del v["mappings"]

    BIOREGISTRY_PATH.write_text(
        json.dumps(registry, indent=2, ensure_ascii=False), encoding="utf-8"
    )


if __name__ == "__main__":
    main()
