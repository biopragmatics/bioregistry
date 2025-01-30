"""Add descriptions from a google curation sheet."""

import click
import pandas as pd

import bioregistry

URL = (
    "https://docs.google.com/spreadsheets/d/e/2PACX-1vQVw4odnZF34f267p9WqdQOhi"
    "Y9tewD-jbnATgpi5W9smbkemvbOcVZSdeboXknoWxDhPyvtcxUYiQO/pub?gid=1947246172&single=true&output=tsv"
)


@click.command()
def main():
    """Add descriptions from a google curation sheet."""
    df = pd.read_csv(URL, sep="\t")
    del df[df.columns[0]]
    df = df[df.description.notna()]
    df = df[df["prefix"].map(lambda p: bioregistry.get_description(p) is None)]
    df = df[df["prefix"].map(lambda p: bioregistry.get_obofoundry_prefix(p) is None)]
    click.echo(df.to_markdown())
    r = dict(bioregistry.read_registry())
    for prefix, description in df[["prefix", "description"]].values:
        r[prefix].description = description
    bioregistry.write_registry(r)


if __name__ == "__main__":
    main()
