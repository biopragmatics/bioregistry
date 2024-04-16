"""Get a curation sheet for recently failing prefixes from the Bioregistry Health Report.

.. seealso:: https://biopragmatics.github.io/bioregistry/health/
"""

from pathlib import Path

import click
import pandas as pd
import yaml

import bioregistry

HERE = Path(__file__).parent.resolve()
ROOT = HERE.parent
HEALTH = ROOT.joinpath("docs", "_data", "health.yaml")
OUTPUT_PATH = Path("~/Desktop/bioregistry_health_report_failures.tsv").expanduser()


def _get_df() -> pd.DataFrame:
    """Get the curation dataframe for recently failing prefixes via the health report."""
    data = yaml.safe_load(HEALTH.read_text())
    most_recent_run = data["runs"][0]
    rows = []
    for result in most_recent_run["results"]:
        if not result["failed"]:
            continue
        prefix = result["prefix"]
        rows.append(
            (
                prefix,
                bioregistry.get_name(prefix),
                bioregistry.get_homepage(prefix),
                result["url"],
                # The following columns are to fill in by the curator
                "",  # call
                "",  # date
                "",  # curator orcid
                "",  # notes
            )
        )

    columns = ["prefix", "name", "homepage", "url", "call", "date", "curator_orcid", "notes"]
    return pd.DataFrame(rows, columns=columns)


@click.command()
@click.option("--path", type=click.Path(), default=OUTPUT_PATH, show_default=True)
def main(path: Path):
    """Write the curation sheet."""
    df = _get_df()
    df.to_csv(path, sep="\t", index=False)


if __name__ == "__main__":
    main()
