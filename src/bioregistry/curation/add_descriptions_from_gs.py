"""Add descriptions from a google curation sheet."""

import click
import pandas as pd

import bioregistry

URL = (
    "https://docs.google.com/spreadsheets/d/e/2PACX-1vQVw4odnZF34f267p9WqdQOhi"
    "Y9tewD-jbnATgpi5W9smbkemvbOcVZSdeboXknoWxDhPyvtcxUYiQO/pub?gid=1947246172&single=true&output=tsv"
)


@click.command()
def main() -> None:
    """Add descriptions from a google curation sheet."""
    df = pd.read_csv(URL, sep="\t")
    del df[df.columns[0]]
    df = df[df.description.notna()]
    df = df[df["prefix"].map(_has_description)]
    df = df[df["prefix"].map(_is_obofoundry)]
    click.echo(df.to_markdown())
    r = dict(bioregistry.read_registry())
    for prefix, description in df[["prefix", "description"]].values:
        r[prefix].description = description
    bioregistry.write_registry(r)


def _has_description(prefix: str) -> bool:
    return bioregistry.get_description(prefix) is None


def _is_obofoundry(prefix: str) -> bool:
    return bioregistry.get_obofoundry_prefix(prefix) is None


if __name__ == "__main__":
    main()
