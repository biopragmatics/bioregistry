"""Import TIB Terminology Service collections into the corresponding Bioregistry collections."""

from collections import Counter

import click
import requests
from tabulate import tabulate
from tqdm import tqdm

import bioregistry
from bioregistry.external.ols.tib import get_tib_ts
from bioregistry.schema_utils import get_collection_mappings

# Add additional mappings in collections.json's `mappings` field, e.g., with
# `tib.collection` as a prefix for TIB OLS collections
KEYWORD_TO_COLLECTION = {v: k for k, v in get_collection_mappings("tib.collection").items()}

BARTOC_TO_COLLECTION = {v: k for k, v in get_collection_mappings("bartoc").items()}


def _import_tib() -> None:
    counter: Counter[str] = Counter()

    tib_to_internal = bioregistry.get_registry_invmap("tib")

    for tib_prefix, tib_data in get_tib_ts().items():
        internal_prefix = tib_to_internal.get(tib_prefix)
        if not internal_prefix:
            tqdm.write(f"no mapping from {tib_prefix}")
            continue
        for keyword in tib_data.get("keywords", []):
            collection = KEYWORD_TO_COLLECTION.get(keyword.lower())
            if not collection:
                counter[keyword.lower()] += 1
                continue
            bioregistry.add_to_collection(collection, internal_prefix)

    bioregistry.manager.write_collections()
    tqdm.write(tabulate(counter.most_common(), headers=["unmapped keyword", "count"]))


def _import_bartoc():
    requests.get(URL)


@click.command()
def main() -> None:
    """Populate collections based on keywords from the TIB terminology service."""
    # _import_tib()
    _import_bartoc()


if __name__ == "__main__":
    main()
