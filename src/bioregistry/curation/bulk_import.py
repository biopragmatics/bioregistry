"""A script for doing bulk import.

If you have a local file or remote file accessible by HTTP/HTTPS/FTP, you can use the
`--path` option like in:

.. code-block:: shell

    $ python -m bioregistry.curation.bulk_google_import --path <your file path>

If you are doing curation on Google Sheets, you can copy the sheet identifier and use
the `--google-sheet` option like in:

.. code-block:: shell

    $ python -m bioregistry.curation.bulk_google_import --google-sheet 10MPt-H6My33mOa1V_VkLh4YG8609N7B_Dey0CBnfTL4
"""

from __future__ import annotations

import sys
from collections import defaultdict
from collections.abc import Mapping
from typing import Any

import click
import pandas as pd

from bioregistry import Resource
from bioregistry.schema_utils import add_resource
from bioregistry.utils import norm

NESTED = {"contact", "contributor"}


def _resource_from_row(row: Mapping[str, Any]) -> Resource:
    kwargs = {}
    nested: defaultdict[str, dict[str, str]] = defaultdict(dict)
    for key, value in row.items():
        if pd.isna(value):
            continue
        key = key.split(" ")[0]  # get rid of all of the "(optional)" labels
        subkeys = key.split("_")
        if subkeys[0] in NESTED:
            k1, k2 = subkeys
            nested[k1][k2] = value
        else:
            kwargs[key] = value
    kwargs.update(nested)
    prefix = kwargs.pop("prefix")
    prefix_norm = norm(prefix)
    if prefix == prefix_norm:
        kwargs["prefix"] = prefix
    else:
        kwargs["prefix"] = prefix_norm
        kwargs.setdefault("synonyms", []).append(prefix)
        kwargs["synonyms"] = sorted(kwargs["synonyms"])

    return Resource(**kwargs)


def _bulk_import_df(df: pd.DataFrame) -> None:
    for _, row in df.iterrows():
        resource = _resource_from_row(row.to_dict())
        try:
            add_resource(resource)
        except KeyError as e:
            click.secho(str(e).strip("'"))
            continue


@click.command()
@click.option("--google-sheet")
@click.option("--google-sheet-gid", type=int, default=0)
@click.option("--path")
def main(google_sheet: str | None, google_sheet_gid: int, path: str | None) -> None:
    """Import prefixes from a google sheet in bulk."""
    # google_sheet = "10MPt-H6My33mOa1V_VkLh4YG8609N7B_Dey0CBnfTL4"
    if google_sheet:
        url = f"https://docs.google.com/spreadsheets/d/{google_sheet}/export?format=tsv&gid={google_sheet_gid}"
        df = pd.read_csv(url, sep="\t")
    elif path:
        df = pd.read_csv(path, sep="," if path.endswith("csv") else "\t")
    else:
        click.secho("no sheet provided", fg="red")
        raise sys.exit(1)

    _bulk_import_df(df)


if __name__ == "__main__":
    main()
