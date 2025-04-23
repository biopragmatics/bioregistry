"""A script to generate summaries and text for the Bioregistry manuscript."""

from __future__ import annotations

import datetime
from collections import defaultdict
from collections.abc import Mapping
from dataclasses import dataclass
from itertools import combinations
from textwrap import dedent
from typing import TYPE_CHECKING, cast

import click
from more_click import force_option
from typing_extensions import Self

from bioregistry import manager
from bioregistry.constants import TABLES_SUMMARY_LATEX_PATH
from bioregistry.version import get_version

if TYPE_CHECKING:
    import pandas as pd


@dataclass
class BioregistrySummary:
    """A container for high-level statistics on the Bioregistry."""

    number_prefixes: int
    number_registries: int
    number_registries_aligned: int
    number_prefixes_novel: int
    number_prefixes_curated: int
    number_mappings: int
    number_synonyms: int
    number_mismatches_curated: int
    number_collections: int
    number_contexts: int
    number_direct_contributors: int
    number_total_contributors: int
    external_sizes: Mapping[str, int]
    date: datetime.datetime

    @property
    def datetime_str(self) -> str:
        """Get the date as an ISO 8601 string."""
        return self.date.strftime("%Y-%m-%d")

    def get_text(self) -> str:
        """Write the introduction summary sentence."""
        remaining = self.number_prefixes - self.number_prefixes_novel
        return (
            dedent(
                f"""\
        The Bioregistry ({get_version()}; {self.datetime_str}) integrates content from and aligns
        {self.number_registries_aligned:,} external registries and contains {self.number_prefixes:,}
        individual records. These records extend on each prior registry
        (e.g., 838 records in {self.external_sizes["prefixcommons"]}, {self.external_sizes["miriam"]:,}
        in MIRIAM/Identifiers.org, and {self.external_sizes["n2t"]:,}  in Name-to-Thing (Wimalaratne et al., 2018),
        each accessed on {self.datetime_str}), as well as the aligned registries combined:
        {self.number_prefixes_novel:,} of the Bioregistry's {self.number_prefixes:,} records are novel,
        i.e. they do not appear in any existing registry. The Bioregistry also adds novel curated metadata
        for {self.number_prefixes_curated:,} of the remaining {remaining:,} records
        ({self.number_prefixes_curated / remaining:.0%} of all records).
        """
            )
            .strip()
            .replace("\n", " ")
        )

    def _table_rows(self) -> list[tuple[str, str | int]]:
        return [
            ("Version", get_version()),
            ("Registries Surveyed", self.number_registries),
            ("Registries Aligned", self.number_registries_aligned),
            ("Prefixes", self.number_prefixes),
            ("Synonyms", self.number_synonyms),
            ("Cross-registry Mappings", self.number_mappings),
            ("Curated Mismatches", self.number_mismatches_curated),
            ("Collections and Contexts", self.number_collections + self.number_contexts),
            ("Direct Contributors", self.number_direct_contributors),
            ("Total Contributors", self.number_total_contributors),
        ]

    def _table_df(self) -> pd.DataFrame:
        import pandas as pd

        return pd.DataFrame(self._table_rows(), columns=["Category", "Count"])

    def get_table_text(self, tablefmt: str = "github") -> str:
        """Get the text version of table 1 in the manuscript."""
        from tabulate import tabulate

        df = self._table_df()
        return tabulate(df.values, headers=list(df.columns), tablefmt=tablefmt)

    def get_table_latex(self) -> str:
        """Get the latex for table 1 in the manuscript."""
        return cast(
            str,
            self._table_df().to_latex(
                index=False,
                caption=f"Overview statistics of the Bioregistry on {self.datetime_str}.",
                label="tab:bioregistry-summary",
                bold_rows=True,
                column_format="lr",
            ),
        )

    @classmethod
    def make(cls, force_download: bool = False) -> Self:
        """Instantiate the class."""
        registry = manager.registry

        metaprefix_to_mapping_count = manager.count_mappings()

        #: The total number of mappings from all records to all external records
        total_mapping_count = sum(metaprefix_to_mapping_count.values())

        #: The total number of synonyms across all records
        synonym_count = sum(
            len(resource.synonyms) for resource in registry.values() if resource.synonyms
        )

        #: The number of prefixes that have no mappings to external registries
        novel_prefixes = {prefix for prefix, entry in registry.items() if not entry.mappings}
        number_novel_prefixes = len(novel_prefixes)

        metaprefixes = set(manager.metaregistry)
        metaprefixes_aligned = set(metaprefix_to_mapping_count)

        #: The number of prefixes that have any overrides that are not novel to the Bioregistry
        prefixes_curated = sum(
            any(
                x not in metaprefixes
                for x, v in entry.model_dump().items()
                if v is not None and x not in {"prefix", "mappings"}
            )
            for prefix, entry in registry.items()
            if prefix not in novel_prefixes
        )

        from bioregistry.external import GETTERS

        return cls(
            date=datetime.datetime.now(),
            number_prefixes=len(registry),
            number_registries=len(metaprefixes),
            number_registries_aligned=len(metaprefixes_aligned),
            number_prefixes_novel=number_novel_prefixes,
            number_mappings=total_mapping_count,
            number_synonyms=synonym_count,
            number_prefixes_curated=prefixes_curated,
            number_mismatches_curated=sum(len(v.values()) for v in manager.mismatches.values()),
            external_sizes={
                metaprefix: len(getter(force_download=force_download))
                for metaprefix, _, getter in GETTERS
            },
            number_collections=len(manager.collections),
            number_contexts=len(manager.contexts),
            number_direct_contributors=len(manager.read_contributors(direct_only=True)),
            number_total_contributors=len(manager.read_contributors(direct_only=False)),
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

    def get_text(self) -> str:
        """Get the summary text."""
        return (
            dedent(
                f"""\
            The upper bound on the number of one-to-one mappings between prefixes in each pair of
            external registries is {self.pairwise_upper_bound:,}. This decreases by
            {self.pairwise_to_direct_ratio:.1f} times to {self.direct_upper_bound:,} mappings when
            using the Bioregistry as a mapping hub. Of these, {self.direct_upper_bound - self.remaining:,}
            ({(self.direct_upper_bound - self.remaining) / self.direct_upper_bound:.0%}) have been
            curated and {self.remaining:,} ({self.remaining / self.direct_upper_bound:.0%}) remain, but these
            numbers are subject to change dependent on both updates to the Bioregistry and external registries.
            """
            )
            .strip()
            .replace("\n", " ")
        )

    @classmethod
    def make(cls, force_download: bool = False) -> Self:
        """Instantiate the class."""
        from bioregistry.external import GETTERS

        registry_to_prefixes = {
            metaprefix: set(getter(force_download=force_download))
            for metaprefix, _, getter in GETTERS
        }

        total_pairwise_upper_bound = sum(
            len(x) * len(y) for x, y in combinations(registry_to_prefixes.values(), 2)
        )
        exclusive_pairwise_upper_bound = sum(
            min(len(x), len(y)) for x, y in combinations(registry_to_prefixes.values(), 2)
        )
        exclusive_direct_upper_bound = sum(len(x) for x in registry_to_prefixes.values())

        registry = manager.registry
        registry_to_mapped_prefixes = defaultdict(set)
        for resource in registry.values():
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


@click.command()
@click.option("--split-lines", is_flag=True)
@force_option  # type:ignore
def _main(split_lines: bool, force: bool) -> None:
    if split_lines:
        from textwrap import fill as _fill
    else:

        def _fill(_s: str) -> str:  # type:ignore
            return _s

    click.echo(_fill(MappingBurdenSummary.make(force_download=force).get_text()) + "\n")
    s = BioregistrySummary.make(force_download=force)
    click.echo(_fill(s.get_text()) + "\n")
    click.echo(s.get_table_text())

    TABLES_SUMMARY_LATEX_PATH.write_text(s.get_table_latex())


if __name__ == "__main__":
    _main()
