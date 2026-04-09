"""Import TIB Terminology Service collections into the corresponding Bioregistry collections."""

from collections import Counter

import click
from tabulate import tabulate
from tqdm import tqdm

import bioregistry
from bioregistry.external.bartoc import get_bartoc, get_bartoc_registries
from bioregistry.external.ols.tib import get_tib_ts
from bioregistry.schema_utils import get_collection_mappings

# Add additional mappings in collections.json's `mappings` field, e.g., with
# `tib.collection` as a prefix for TIB OLS collections
KEYWORD_TO_COLLECTION = {v: k for k, v in get_collection_mappings("tib.collection").items()}


def _import_tib() -> None:
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


def _import_bartoc() -> None:
    rows = []
    bartoc_registries = get_bartoc_registries()
    bartoc_to_internal = bioregistry.get_registry_invmap("bartoc")
    bartoc_data = get_bartoc()

    for collection_id, registry_bartoc_id in get_collection_mappings("bartoc").items():
        for resource_bartoc_id in bartoc_registries[registry_bartoc_id]:
            prefix = bartoc_to_internal.get(resource_bartoc_id)
            if prefix:
                bioregistry.add_to_collection(collection_id, prefix)
            else:
                rows.append((resource_bartoc_id, bartoc_data[resource_bartoc_id].get("name")))
                continue
    bioregistry.manager.write_collections()
    tqdm.write(tabulate(rows, headers=["unmapped BARTOC ID", "name"]))


@click.command()
def main() -> None:
    """Populate collections based on keywords from the TIB terminology service."""
    # _import_tib()
    _import_bartoc()


if __name__ == "__main__":
    main()
