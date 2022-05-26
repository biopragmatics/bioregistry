"""A script to generate summaries and text for the Bioregistry manuscript."""

import datetime
from dataclasses import dataclass
from textwrap import dedent
from typing import Mapping

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


def main():
    summary = BioregistrySummary.make()
    print(summary.paper_text())


if __name__ == "__main__":
    main()
