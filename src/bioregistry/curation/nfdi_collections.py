"""Import TIB Terminology Service collections into the corresponding Bioregistry collections."""

from collections import Counter

import click
from tabulate import tabulate
from tqdm import tqdm

import bioregistry
from bioregistry.external.ols.tib import get_tib_ts

#: A mapping from lowercased keyword to Bioregistry collection
KEYWORD_TO_COLLECTION = {
    "nfdi4cat": "0000011",
    "nfdi4chem": "0000014",
    "nfdi4ing": "0000022",
    "nfdi4culture": "0000025",
    "nfdi4energy": "0000021",
    "dataplant": "0000023",  # nfdi4plant
    "fairmat": "0000024",
}


@click.command()
def main() -> None:
    """Populate collections based on keywords from the TIB terminology service."""
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


if __name__ == "__main__":
    main()
