"""A script for doing bulk import from google sheets."""

from collections import defaultdict
from typing import Any, Mapping

import click
import pandas as pd

from bioregistry import Resource
from bioregistry.schema_utils import add_resource

NESTED = {"contact", "contributor"}


def _resource_from_row(row: Mapping[str, Any]) -> Resource:
    kwargs = {}
    nested = defaultdict(dict)
    for key, value in row:
        key = key.split(" ")[0]  # get rid of all of the "(optional)" labels
        if key in NESTED:
            k1, k2 = key.split("_")
            nested[k1][k2] = value
        else:
            kwargs[key] = value
    kwargs.update(nested)
    return Resource(**kwargs)


@click.command()
@click.argument("sheet")
def main(sheet: str):
    """Import prefixes from a google sheet in bulk."""
    sheet = "10MPt-H6My33mOa1V_VkLh4YG8609N7B_Dey0CBnfTL4"
    url = f"https://docs.google.com/spreadsheets/d/{sheet}/export?format=tsv&gid=0"
    df = pd.read_csv(url, sep="\t")
    for _, row in df.iterrows():
        resource = _resource_from_row(row)
        add_resource(resource)


if __name__ == '__main__':
    main()
