"""A script to generate summaries and text for the Bioregistry manuscript."""

import datetime
from collections import defaultdict
from dataclasses import dataclass
from itertools import combinations
from textwrap import dedent
from typing import Mapping

from humanize import intword
from rich import print

import bioregistry
from bioregistry.external import GETTERS
from bioregistry.version import get_version


@dataclass
class BioregistrySummary:
    """A container for high-level statistics on the Bioregistry."""

    number_prefixes: int
    number_registries: int
    number_prefixes_novel: int
    number_prefixes_curated: int
    number_mappings: int
    number_synonyms: int
    number_mismatches_curated: int
    external_sizes: Mapping[str, int]
    date: datetime.datetime

    @property
    def datetime_str(self) -> str:
        """Get the date as an ISO 8601 string."""
        return self.date.strftime("%Y-%m-%d")

    def print(self) -> None:
        """Print the summary."""
        print(f"Date: {self.datetime_str}")
        print("Prefixes", self.number_prefixes)
        print("Prefixes - Novel", self.number_prefixes_novel)
        print("Prefixes - Curated", self.number_prefixes_curated)
        print("Mappings", self.number_mappings)
        print("Synonyms", self.number_synonyms)
        print("Registries", self.number_registries)
        print("Mismatches", self.number_mismatches_curated)
        for metaprefix, size in sorted(self.external_sizes.items()):
            print(f"{bioregistry.get_registry_short_name(metaprefix)} size", size)

    def paper_text(self):
        """Write the introduction summary sentence."""
        remaining = self.number_prefixes - self.number_prefixes_novel
        return (
            dedent(
                f"""\
        The Bioregistry (v{get_version()}) integrates {self.number_registries:,} external registries
        and contains {self.number_prefixes:,} records, compared to {self.external_sizes['prefixcommons']}
        records in Prefix Commons, {self.external_sizes['miriam']:,} in MIRIAM/Identifiers.org, and
        {self.external_sizes['n2t']:,} in Name-to-Thing (each accessed on {self.datetime_str}).
        {self.number_prefixes_novel:,} of the {self.number_prefixes:,} records are novel (i.e., they do not
        appear in any external registry) and the Bioregistry adds additional novel curated metadata to
        {self.number_prefixes_curated:,} of the remaining
        {remaining:,} records ({self.number_prefixes_curated / remaining:.0%}).
        """
            )
            .strip()
            .replace("\n", " ")
        )

    @classmethod
    def make(cls):
        """Instantiate the class."""
        registry = bioregistry.read_registry()

        #: The total number of mappings from all records to all external records
        mapping_count = sum(len(entry.mappings) for entry in registry.values() if entry.mappings)

        #: The total number of synonyms across all records
        synonym_count = sum(
            len(resource.synonyms) for resource in registry.values() if resource.synonyms
        )

        #: The number of prefixes that have no mappings to external registries
        novel_prefixes = {prefix for prefix, entry in registry.items() if not entry.mappings}
        number_novel_prefixes = len(novel_prefixes)

        metaprefixes = set(bioregistry.read_metaregistry())

        #: The number of prefixes that have any overrides that are not novel to the Bioregistry
        prefixes_curated = sum(
            any(
                x not in metaprefixes
                for x, v in entry.dict().items()
                if v is not None and x not in {"prefix", "mappings"}
            )
            for prefix, entry in registry.items()
            if prefix not in novel_prefixes
        )

        return cls(
            date=datetime.datetime.now(),
            number_prefixes=len(registry),
            number_registries=len(metaprefixes),
            number_prefixes_novel=number_novel_prefixes,
            number_mappings=mapping_count,
            number_synonyms=synonym_count,
            number_prefixes_curated=prefixes_curated,
            number_mismatches_curated=sum(len(v) for v in bioregistry.read_mismatches().values()),
            external_sizes={metaprefix: len(getter()) for metaprefix, _, getter in GETTERS},
        )


@dataclass
class MappingBurdenSummary:
    """A container for high-level statistics on the remaining mappings to be curated in the Bioregistry."""

    #: This value is a bit of a strawman - it counts the total number of possible matches that could exist
    #: between elements in all possible pairs of external registries. In reality, mappings should be
    #: one-to-one (for the most part), meaning that once an element in one registry is mapped, it won't be
    #: mapped to another one. This quadratically reduces the number in our estimate.
    total_pairwise_upper_bound: int
    pairwise_upper_bound: int
    direct_upper_bound: int
    remaining: int

    @property
    def pairwise_to_direct_ratio(self) -> float:
        """Get the ratio between pairwise curation and direct curation."""
        return self.pairwise_upper_bound / self.direct_upper_bound

    def print(self):
        """Print the summary."""
        print(
            dedent(
                f"""\
            While there is an upper bound of {intword(self.total_pairwise_upper_bound)} possible pairs of
            records between pairs of external registries, there is a more realistic upper bound of
            {self.pairwise_upper_bound:,} when assuming mappings between each pair of registries
            are one-to-one. When using the Bioregistry as a hub for mappings, this upper bound
            decreases by {self.pairwise_to_direct_ratio:.1f} times to {self.direct_upper_bound:,}.
            Of these, a total of {self.remaining:,} ({self.remaining/self.direct_upper_bound:.0%})
            mappings remain to be curated.
            """
            )
            .strip()
            .replace("\n", " ")
        )

    @classmethod
    def make(cls):
        """Instantiate the class."""
        registry_to_prefixes = {metaprefix: set(getter()) for metaprefix, _, getter in GETTERS}

        total_pairwise_upper_bound = sum(
            len(x) * len(y) for x, y in combinations(registry_to_prefixes.values(), 2)
        )
        exclusive_pairwise_upper_bound = sum(
            min(len(x), len(y)) for x, y in combinations(registry_to_prefixes.values(), 2)
        )
        exclusive_direct_upper_bound = sum(len(x) for x in registry_to_prefixes.values())
        ratio = exclusive_pairwise_upper_bound / exclusive_direct_upper_bound

        registry = bioregistry.read_registry()
        registry_to_mapped_prefixes = defaultdict(set)
        for prefix, resource in registry.items():
            for metaprefix, external_prefix in resource.get_mappings().items():
                registry_to_mapped_prefixes[metaprefix].add(external_prefix)

        # Get the set of prefixes for each external registry that haven't been
        # mapped to the Bioregistry
        registry_to_unmapped_prefixes = {
            metaprefix: external_prefixes - registry_to_mapped_prefixes[metaprefix]
            for metaprefix, external_prefixes in registry_to_prefixes.items()
        }
        remaining = sum(len(v) for v in registry_to_unmapped_prefixes.values())

        return cls(
            total_pairwise_upper_bound=total_pairwise_upper_bound,
            pairwise_upper_bound=exclusive_pairwise_upper_bound,
            direct_upper_bound=exclusive_direct_upper_bound,
            remaining=remaining,
        )


def _main():
    MappingBurdenSummary.make().print()
    print()
    print(BioregistrySummary.make().paper_text())


if __name__ == "__main__":
    _main()
