"""Show discrepancies between Bioregistry and OBO Foundry deprecation status."""

import click
import pandas as pd

import bioregistry


@click.command()
def main() -> None:
    """Show discrepancies between Bioregistry and OBO Foundry deprecation status."""
    rows = []
    for prefix, resource in bioregistry.read_registry().items():
        if resource.obofoundry is None and resource.miriam:
            continue
        # no additional judgement was passed in curation of the Bioregistry
        if resource.deprecated is None:
            continue

        obo_deprecation = (
            None if resource.obofoundry is None else resource.obofoundry.get("deprecated", False)
        )
        miriam_deprecation = (resource.miriam or {}).get("deprecated")

        if obo_deprecation is not None and miriam_deprecation is not None:
            if resource.deprecated != obo_deprecation or resource.deprecated != miriam_deprecation:
                rows.append((prefix, resource.deprecated, obo_deprecation, miriam_deprecation))
        elif obo_deprecation is not None:
            if resource.deprecated != obo_deprecation:
                rows.append((prefix, resource.deprecated, obo_deprecation, "-"))
        elif miriam_deprecation is not None:
            if resource.deprecated != miriam_deprecation:
                rows.append((prefix, resource.deprecated, "-", miriam_deprecation))

    df = pd.DataFrame(rows, columns=["prefix", "bioregistry", "obo", "miriam"])
    click.echo(df.to_markdown())


if __name__ == "__main__":
    main()
