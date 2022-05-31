"""A script for doing bulk import from google sheets."""

from collections import defaultdict
from typing import Any, Mapping

import click
import pandas as pd

from bioregistry import Resource
from bioregistry.schema_utils import add_resource
from bioregistry.utils import norm

NESTED = {"contact", "contributor"}


def _resource_from_row(row: Mapping[str, Any]) -> Resource:
    kwargs = {}
    nested = defaultdict(dict)
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


def _bulk_import_df(df: pd.DataFrame):
    for _, row in df.iterrows():
        row: pd.Series
        resource = _resource_from_row(row.to_dict())
        try:
            add_resource(resource)
        except KeyError as e:
            click.secho(str(e).strip("'"))
            continue


@click.command()
@click.option("--sheet", required=True)
def main(sheet: str):
    """Import prefixes from a google sheet in bulk."""
    # sheet = "10MPt-H6My33mOa1V_VkLh4YG8609N7B_Dey0CBnfTL4"
    url = f"https://docs.google.com/spreadsheets/d/{sheet}/export?format=tsv&gid=0"
    df = pd.read_csv(url, sep="\t")
    _bulk_import_df(df)


if __name__ == "__main__":
    main()
