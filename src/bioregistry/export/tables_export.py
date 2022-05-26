# -*- coding: utf-8 -*-

"""Make tables exports."""

from textwrap import dedent

import click
import pandas as pd

import bioregistry
from bioregistry.constants import (
    TABLES_GOVERNANCE_LATEX_PATH,
    TABLES_GOVERNANCE_TSV_PATH,
    TABLES_SUMMARY_LATEX_PATH,
)
from bioregistry.summary import BioregistrySummary

__all__ = [
    "export_tables",
]

GOVERNANCE_COLUMNS = [
    "Name",
    "Scope",
    "Status",
    "Imports External Prefixes",
    "Curates Novel Prefixes",
    "Accepts External Contributions",
    "Uses Public Version Control",
    "Has Public Review Team",
]


def _render_bool(x: bool, true_value: str = "✓", false_value: str = "") -> str:
    return true_value if x else false_value


def _replace_na(s: str) -> str:
    if s.lower() == "n/a":
        return ""
    return s


def _governance_df() -> pd.DataFrame:
    rows = []
    for registry in bioregistry.read_metaregistry().values():
        rows.append(
            (
                registry.get_short_name(),
                registry.governance.scope.title(),
                registry.governance.status.title(),
                _render_bool(registry.governance.imports),
                _render_bool(registry.governance.curates),
                _render_bool(registry.governance.accepts_external_contributions),
                _render_bool(registry.governance.public_version_control),
                registry.governance.review_team_icon,
            )
        )
    return pd.DataFrame(rows, columns=GOVERNANCE_COLUMNS)


@click.command()
def export_tables():
    """Export tables.

    1. TODO: Export data model comparison, see also https://bioregistry.io/related#data-models
    2. Export governance comparison, see also https://bioregistry.io/related#governance
    """
    df = _governance_df()
    df.to_csv(TABLES_GOVERNANCE_TSV_PATH, sep="\t", index=False)
    TABLES_GOVERNANCE_LATEX_PATH.write_text(
        df.to_latex(
            index=False,
            bold_rows=True,
            label="tab:registry-comparison-governance",
            caption=dedent(
                """\
               A survey of registries' governance and maintenance models. The scope column describes the
               kinds of prefixes contained within the registry. The status column is active if the registry
               is currently being maintained and is responsive to public external feedback, unresponsive if
               the registry is currently being maintained but is not responsive to public external feedback,
               and inactive otherwise. The imports external prefixes column denotes if the registry reuses
               and harmonizes content from external registries. The curates novel prefixes column denotes
               whether novel curation of prefixes and their associated metadata is done for the registry.
               The accepts external contributions column denotes whether the registry has both the governance
               model and technical infrastructure for accepting external contributions in the form of the
               suggestion of new prefixes, improvement to metadata associated with existing prefixes, etc.
               The uses public version control column denotes whether the data underlying the registry and/or
               its associated code are stored in a publicly accessible version-controlled system (e.g., git
               via GitHub). The has public review team column denotes whether there is a publicly accessible
               list of the reviewers. Asterisks in this column denote that rather than an explicit list, the
               reviewers can be inferred through the registry's version control system.
            """
            )
            .strip()
            .replace("\n", " "),
        ),
        encoding="utf-8",
    )

    s = BioregistrySummary.make()
    TABLES_SUMMARY_LATEX_PATH.write_text(s.get_table_latex())


if __name__ == "__main__":
    export_tables()
