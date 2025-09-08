"""Make a curation sheet for the bioregistry."""

import click
import pandas as pd

import bioregistry
from bioregistry.constants import BIOREGISTRY_MODULE


def descriptions() -> None:
    """Make a curation sheet for descriptions."""
    columns = [
        "prefix",
        "name",
        "homepage",
        "description",
    ]
    path = BIOREGISTRY_MODULE.join("curation", name="descriptions.tsv")
    rows = []
    for prefix in bioregistry.read_registry():
        if bioregistry.get_description(prefix):
            continue
        if bioregistry.is_deprecated(prefix):
            continue
        rows.append(
            (
                prefix,
                bioregistry.get_name(prefix),
                bioregistry.get_homepage(prefix),
                "",
            )
        )
    df = pd.DataFrame(rows, columns=columns)
    click.echo(f"Writing {len(df.index)} description rows to {path}")
    df.to_csv(path, sep="\t", index=False)


def examples() -> None:
    """Make a curation sheet for examples."""
    columns = [
        "prefix",
        "name",
        "homepage",
        "deprecated",
        "example",
    ]
    rows = []
    for prefix in bioregistry.read_registry():
        if bioregistry.get_example(prefix):
            continue
        homepage = bioregistry.get_homepage(prefix)
        if homepage is None:
            continue
        deprecated = bioregistry.is_deprecated(prefix)
        rows.append(
            (
                prefix,
                bioregistry.get_name(prefix),
                homepage,
                "x" if deprecated else "",
                "",
            )
        )
    df = pd.DataFrame(rows, columns=columns)
    path = BIOREGISTRY_MODULE.join("curation", name="examples.tsv")
    click.echo(f"Outputting {len(df.index)} example rows to {path}")
    df.to_csv(path, sep="\t", index=False)


def homepages() -> None:
    """Make a curation sheet for homepages."""
    columns = [
        "prefix",
        "name",
        "deprecated",
        "homepage",
    ]
    path = BIOREGISTRY_MODULE.join("curation", name="homepages.tsv")
    rows = []
    for prefix in bioregistry.read_registry():
        homepage = bioregistry.get_homepage(prefix)
        if homepage is not None:
            continue
        deprecated = bioregistry.is_deprecated(prefix)
        rows.append(
            (
                prefix,
                bioregistry.get_name(prefix),
                "x" if deprecated else "",
                homepage,
            )
        )
    df = pd.DataFrame(rows, columns=columns)
    click.echo(f"Outputting {len(df.index)} homepage rows to {path}")
    df.to_csv(path, sep="\t", index=False)


if __name__ == "__main__":
    descriptions()
    examples()
    homepages()
