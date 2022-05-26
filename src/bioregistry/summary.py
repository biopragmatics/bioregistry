import datetime
from dataclasses import dataclass
from typing import Mapping

import bioregistry
from bioregistry.external import GETTERS


@dataclass
class BioregistrySummary:
    number_prefixes: int
    number_registries: int
    number_prefixes_novel: int
    number_prefixes_curated: int
    number_prefix_curations: int
    number_mappings: int
    number_synonyms: int
    number_mismatches_curated: int
    external_sizes: Mapping[str, int]
    date: datetime.datetime

    @property
    def datetime_str(self) -> str:
        return self.date.strftime("%Y-%m-%d")

    def print(self) -> None:
        """Print the information"""
        print(f"Date: {self.datetime_str}")
        print("Prefixes", self.number_prefixes)
        print("Prefixes - Novel", self.number_prefixes_novel)
        print("Prefixes - Curated", self.number_prefixes_curated,
              f"({self.number_prefix_curations} total, {self.number_prefix_curations / self.number_prefixes_curated:.2} on average)"
              )
        print("Mappings", self.number_mappings)
        print("Synonyms", self.number_synonyms)
        print("Registries", self.number_registries)
        print("Mismatches", self.number_mismatches_curated)
        for metaprefix, size in sorted(self.external_sizes.items()):
            print(f"{bioregistry.get_registry_short_name(metaprefix)} size", size)


def get():
    registry = bioregistry.read_registry()

    #: The total number of mappings from all records to all external records
    mapping_count = sum(
        len(entry.mappings)
        for entry in registry.values()
        if entry.mappings
    )

    #: The total number of synonyms across all records
    synonym_count = sum(
        len(resource.synonyms)
        for resource in registry.values()
        if resource.synonyms
    )

    #: The number of prefixes that have no mappings to external registries
    number_novel_prefixes = sum(not entry.mappings for entry in registry.values())

    metaprefixes = set(bioregistry.read_registry())

    #: The number of prefixes that have any overrides
    prefixes_curated = sum(
        any(
            x not in metaprefixes
            for x, v in entry.dict().items()
            if v is not None and x not in {"prefix", "mappings"}
        )
        for entry in registry.values()
    )

    #: The total number of overrides
    prefix_curations = sum(
        sum(
            x not in metaprefixes
            for x, v in entry.dict().items()
            if v is not None and x not in {"prefix", "mappings"}
        )
        for entry in registry.values()
    )

    return BioregistrySummary(
        date=datetime.datetime.now(),
        number_prefixes=len(registry),
        number_registries=len(metaprefixes),
        number_prefixes_novel=number_novel_prefixes,
        number_mappings=mapping_count,
        number_synonyms=synonym_count,
        number_prefixes_curated=prefixes_curated,
        number_prefix_curations=prefix_curations,
        number_mismatches_curated=sum(len(v) for v in bioregistry.read_mismatches().values()),
        external_sizes={
            metaprefix: len(getter())
            for metaprefix, _, getter in GETTERS
        },
    )


def main():
    get().print()


if __name__ == '__main__':
    main()
