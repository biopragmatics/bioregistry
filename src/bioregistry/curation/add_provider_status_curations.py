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

        # FIXME need to handle the fact that google stripped all
        #  lefthand zeros from the example
        uri_format = url.replace(example, "$1")

        resource = manager.get_resource(prefix, strict=True)
        if not resource.providers:
            continue

        tqdm.write(f"[{prefix}] - {uri_format}")

        for provider in resource.providers:
            if provider.uri_format == uri_format:
                tqdm.write(f"[{prefix} - {provider.code}] - {uri_format}")
            if provider.uri_format == uri_format and call != "available":
                provider.status = StatusCheck(
                    value=call,
                    date=date,
                    contributor=curator_orcid,
                    notes=notes,
                )

    manager.write_registry()


if __name__ == "__main__":
    add_provider_status_curations()
