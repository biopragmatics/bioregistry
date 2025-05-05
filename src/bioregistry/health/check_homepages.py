"""A script to check which homepages in entries in the Bioregistry actually can be accessed."""

from __future__ import annotations

import sys
from collections import defaultdict
from datetime import datetime

import click
import pandas as pd
import requests
from tqdm import tqdm
from tqdm.contrib.concurrent import thread_map

import bioregistry

__all__ = [
    "main",
]


def _process(element: tuple[str, set[str]]) -> tuple[str, set[str], bool, str | None]:
    homepage, prefixes = element
    if "github.com" in homepage:  # skip github links for now
        return homepage, prefixes, False, None
    if "purl.obolibrary.org" in homepage:  # this is never acceptable
        return homepage, prefixes, True, "no PURLs allowed"

    failed = False
    msg = ""
    try:
        res = requests.get(homepage, timeout=10)
    except OSError as e:
        failed = True
        msg = e.__class__.__name__
    else:
        if res.status_code != 200:
            failed = True
            msg = f"status: {res.status_code}"
    if failed:
        with tqdm.external_write_mode():
            click.echo(
                f"[{datetime.now().strftime('%H:%M:%S')}] "
                + click.style(", ".join(sorted(prefixes)), fg="green")
                + " at "
                + click.style(homepage, fg="red")
                + " failed to download: "
                + click.style(msg, fg="bright_black")
            )
    return homepage, prefixes, failed, msg


@click.command()
def main() -> None:
    """Run the homepage health check script."""
    homepage_to_prefixes = defaultdict(set)
    for prefix in bioregistry.read_registry():
        if bioregistry.is_deprecated(prefix):
            continue
        homepage = bioregistry.get_homepage(prefix)
        if homepage is None:
            continue
        homepage_to_prefixes[homepage].add(prefix)

    rv = thread_map(_process, list(homepage_to_prefixes.items()), desc="Checking homepages")  # type:ignore[no-untyped-call]

    failed = sum(failed for _, _, failed, _ in rv)
    click.secho(
        f"{failed}/{len(rv)} ({failed / len(rv):.2%}) homepages failed to load", fg="red", bold=True
    )

    df = pd.DataFrame(
        columns=["prefix", "homepage", "message"],
        data=[
            (prefix, homepage, msg)
            for homepage, prefixes, failed, msg in rv
            if failed
            for prefix in prefixes
        ],
    )
    click.echo(df.to_markdown())
    sys.exit(1 if 0 < failed else 0)


if __name__ == "__main__":
    main()
