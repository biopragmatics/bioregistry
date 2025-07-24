"""Add provider status curations.

Added by https://github.com/biopragmatics/bioregistry/pull/1615.
"""

import click
import pandas as pd
from tqdm import tqdm

from bioregistry import manager
from bioregistry.schema.struct import StatusCheck

URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSC8RAMlNGauLHJb1RGwFuvC2LBJBjeeICRtq596npE6G4ZjZwX8W_Fz031hAfqsbu6f9Ruxl2PTsFx/pub?gid=1207894592&single=true&output=tsv"


@click.command()
@click.option("--url", default=URL)
def add_provider_status_curations(url: str) -> None:
    """Add provider status curations."""
    cols = ["prefix", "example_luid", "url", "call", "date", "curator_orcid", "notes"]
    df = pd.read_csv(url, sep="\t", dtype=str)
    for prefix, example, url, call, date, curator_orcid, notes in df[cols].values:
        if pd.isna(example):
            tqdm.write(f"[{prefix}] missing example")
            continue
        if pd.isna(url):
            tqdm.write(f"[{prefix}] missing url")
            continue

        resource = manager.get_resource(prefix, strict=True)
        if not resource.providers:
            continue

        resource_example = resource.get_example(strict=True)
        if not resource_example.endswith(example):
            tqdm.write(
                f"[{prefix}] PROBLEM WITH EXAMPLE. {example} in sheet, {resource_example} in bioregistry"
            )
            continue

        uri_format = url.replace(resource_example, "$1")

        for provider in resource.providers:
            if provider.uri_format != uri_format:
                continue
            if call == "available":
                tqdm.write(f"[{prefix}] skipping available")
                continue
            provider.status = StatusCheck(
                value=call,
                date=date,
                contributor=curator_orcid,
                notes=notes,
            )

    manager.write_registry()


if __name__ == "__main__":
    add_provider_status_curations()
