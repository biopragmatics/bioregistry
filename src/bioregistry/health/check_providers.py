# -*- coding: utf-8 -*-

"""A script to check which providers in entries in the Bioregistry actually can be accessed."""

import sys
from datetime import datetime
from typing import Tuple

import click
import pandas as pd
import requests
from tqdm import tqdm
from tqdm.contrib.concurrent import thread_map

import bioregistry
from bioregistry.utils import secho

__all__ = [
    "main",
]


def _process(element: Tuple[str, str, str]) -> Tuple[str, str, str, bool, str]:
    prefix, example, url = element

    failed = False
    msg = ""
    try:
        res = requests.get(url, timeout=10)
    except IOError as e:
        failed = True
        msg = e.__class__.__name__
    else:
        if res.status_code != 200:
            failed = True
            msg = f"status: {res.status_code}"
    if failed:
        with tqdm.external_write_mode():
            click.echo(
                f'[{datetime.now().strftime("%H:%M:%S")}] '
                + click.style(prefix, fg="green")
                + " at "
                + click.style(url, fg="red")
                + " failed to download: "
                + click.style(msg, fg="bright_black")
            )
    return prefix, example, url, failed, msg


@click.command()
def main():
    """Run the provider health check script."""
    rows = []
    for prefix in bioregistry.read_registry():
        if bioregistry.is_deprecated(prefix):
            continue
        example = bioregistry.get_example(prefix)
        if example is None:
            continue

        url = bioregistry.get_iri(prefix, example, use_bioregistry_io=False)
        if url is None:
            secho(f"[{prefix}] failed to generate URL for example {example}", fg="red")
            continue

        rows.append((prefix, example, url))

    rv = thread_map(_process, rows, desc="Checking providers")

    failed = sum(failed for _, _, _, failed, _ in rv)
    click.secho(
        f"{failed}/{len(rv)} ({failed / len(rv):.2%}) providers failed", fg="red", bold=True
    )

    df = pd.DataFrame(
        columns=["prefix", "example", "url", "message"],
        data=[(prefix, example, url, msg) for prefix, example, url, failed, msg in rv if failed],
    )
    click.echo(df.to_markdown())
    sys.exit(1 if 0 < failed else 0)


if __name__ == "__main__":
    main()
