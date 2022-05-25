# -*- coding: utf-8 -*-

"""Make tables exports."""

import click
import pandas as pd

import bioregistry
from bioregistry.constants import TABLES_GOVERNANCE_LATEX_PATH, TABLES_GOVERNANCE_TSV_PATH

__all__ = [
    "export_tables",
]

GOVERNANCE_COLUMNS = [
    "Name",
    "Accepts External Contributions",
    "Public Version Control",
    "Review Team",
    "Scope",
    "Status",
]


def _render_bool(x: bool) -> str:
    return "✓" if x else ""


def _governance_df() -> pd.DataFrame:
    rows = []
    for registry in bioregistry.read_metaregistry().values():
        rows.append((
            registry.get_short_name(),
            _render_bool(registry.governance.accepts_external_contributions),
            _render_bool(registry.governance.public_version_control),
            registry.governance.review_team.title(),
            registry.governance.scope.title(),
            registry.governance.status.title(),
        ))
    return pd.DataFrame(rows, columns=GOVERNANCE_COLUMNS)


@click.command()
def export_tables():
    """Export tables.

    1. TODO: Export data model comparison, see also https://bioregistry.io/related#data-models
    2. Export governance comparison, see also https://bioregistry.io/related#governance
    """
    df = _governance_df()
    df.to_csv(TABLES_GOVERNANCE_TSV_PATH, sep='\t', index=False)
    TABLES_GOVERNANCE_LATEX_PATH.write_text(
        df.to_latex(
            index=False,
            label="registry-comparison-governance",
            caption="Caption of this table, nice",
        ),
        encoding='utf-8',
    )


if __name__ == '__main__':
    export_tables()
