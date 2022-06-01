# -*- coding: utf-8 -*-

"""Script for adding examples automatically."""

import gzip

from pyobo.xrefdb.xrefs_pipeline import MAPPINGS_DB_TSV_CACHE
from tqdm import tqdm

import bioregistry
from bioregistry import get_example, write_registry


def main():
    """Add examples to the bioregistry from Inspector Javert's Xref Database."""
    registry = bioregistry.read_registry()
    missing = {key for key in registry if get_example(key) is None}
    with gzip.open(MAPPINGS_DB_TSV_CACHE, "rt") as file:
        for line in tqdm(file):
            source_ns, source_id, target_ns, target_id, _ = line.strip().split("\t")
            if source_ns in missing:
                registry[source_ns]["example"] = source_id
                tqdm.write(f"added example {source_ns} {source_id}")
                missing.remove(source_ns)
            if target_ns in missing:
                registry[target_ns]["example"] = target_id
                tqdm.write(f"added example {target_ns} {target_id}")
                missing.remove(target_ns)
    write_registry(registry)


if __name__ == "__main__":
    main()
