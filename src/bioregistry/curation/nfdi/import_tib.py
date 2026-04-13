"""Import TIB collections."""

from collections import Counter

import click
from tabulate import tabulate
from tqdm import tqdm

import bioregistry
from bioregistry.external import get_tib_ts
from bioregistry.schema_utils import get_collection_mappings

# Add additional mappings in collections.json's `mappings` field, e.g., with
# `tib.collection` as a prefix for TIB OLS collections
KEYWORD_TO_COLLECTION = {v: k for k, v in get_collection_mappings("tib.collection").items()}


@click.command()
def import_tib() -> None:
    """Import TIB collections."""
    tqdm.write("\n\nImporting Collections from TIB OLS\n\n")
    counter: Counter[str] = Counter()

    tib_to_internal = bioregistry.get_registry_invmap("tib")

    for tib_prefix, tib_data in get_tib_ts().items():
        internal_prefix = tib_to_internal.get(tib_prefix)
        if not internal_prefix:
            tqdm.write(f"no mapping from {tib_prefix}")
            continue
        for keyword in tib_data.get("keywords", []):
            collection_id = KEYWORD_TO_COLLECTION.get(keyword.lower())
            if not collection_id:
                counter[keyword.lower()] += 1
                continue
            bioregistry.add_to_collection(collection_id, internal_prefix)

    bioregistry.manager.write_collections()
    tqdm.write(tabulate(counter.most_common(), headers=["unmapped TIB keyword", "count"]))


if __name__ == "__main__":
    import_tib()
