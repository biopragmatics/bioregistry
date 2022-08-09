# -*- coding: utf-8 -*-

"""A script to check which providers in entries in the Bioregistry actually can be accessed."""

import sys
from datetime import datetime
from typing import Tuple

import click
import pandas as pd
import requests
import yaml
from tqdm import tqdm
from tqdm.contrib.concurrent import thread_map
from tqdm.contrib.logging import logging_redirect_tqdm

import bioregistry
from bioregistry.constants import DOCS_DATA
from bioregistry.utils import secho

__all__ = [
    "main",
]

HEALTH_PATH = DOCS_DATA.joinpath("health.yaml")


def _process(element: Tuple[str, str, str]) -> Tuple[str, str, str, bool, str, str]:
    prefix, example, url = element

    failed = False
    msg = ""
    context = ""
    try:
        res = requests.get(url, timeout=15, allow_redirects=True)
    except IOError as e:
        failed = True
        msg = e.__class__.__name__
        context = str(e)
    else:
        if res.status_code != 200:
            failed = True
            msg = f"HTTP {res.status_code}"
            context = str(res.status_code)
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
    return prefix, example, url, failed, msg, context


@click.command()
def main():
    """Run the provider health check script."""
    rows = []

    for prefix, resource in tqdm(
        sorted(bioregistry.read_registry().items()), desc="Preparing example URLs"
    ):
        if resource.is_deprecated():
            continue
        example = resource.get_example()
        if example is None:
            continue

        url = bioregistry.get_iri(prefix, example, use_bioregistry_io=False)
        if url is None:
            continue

        rows.append((prefix, example, url))

    with logging_redirect_tqdm():
        rv = thread_map(_process, rows, desc="Checking providers")

    failed = sum(failed for _, _, _, failed, _, _ in rv)
    secho(f"{failed}/{len(rv)} ({failed / len(rv):.2%}) providers failed", fg="red", bold=True)

    df = pd.DataFrame(
        columns=[
            "prefix",
            "name",
            "example",
            "url",
            "message",
            "context",
            "contact_name",
            "contact_email",
            "contact_github",
        ],
        data=[
            (
                prefix,
                bioregistry.get_name(prefix),
                example,
                url,
                msg,
                context,
                bioregistry.get_contact_name(prefix),
                bioregistry.get_contact_email(prefix),
                bioregistry.get_contact_github(prefix),
            )
            for prefix, example, url, failed, msg, context in rv
            if failed
        ],
    )
    click.echo(df.to_markdown())
    HEALTH_PATH.write_text(
        yaml.safe_dump(df.to_dict(orient="records"), sort_keys=True, allow_unicode=True)
    )
    sys.exit(1 if 0 < failed else 0)


if __name__ == "__main__":
    main()
