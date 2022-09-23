# -*- coding: utf-8 -*-

"""A script to check which providers in entries in the Bioregistry actually can be accessed."""

import datetime
import sys
from typing import List, Optional, Tuple

import click
import pandas as pd
import requests
import yaml
from pydantic import BaseModel, Field
from tqdm import tqdm
from tqdm.contrib.concurrent import thread_map
from tqdm.contrib.logging import logging_redirect_tqdm

import bioregistry
from bioregistry.constants import DOCS_DATA
from bioregistry.utils import secho

__all__ = [
    "main",
]

HEALTH_YAML_PATH = DOCS_DATA.joinpath("health.yaml")


class ProviderStatus(BaseModel):
    """A container for provider information."""

    prefix: str
    example: str
    url: str
    failed: bool
    message: Optional[str]
    context: Optional[str]
    date: str = Field(default_factory=lambda: datetime.date.today().strftime("%Y-%m-%d"))


class DailySummary(BaseModel):
    date: str
    total_measured: int
    failure_percent: float = Field(
        ge=0.0, le=100.00, description="The percentage of providers that did not successfully ping."
    )


class Database(BaseModel):
    results: List[ProviderStatus]
    daily_summaries: List[DailySummary]


@click.command()
def main():
    """Run the provider health check script."""
    if HEALTH_YAML_PATH.is_file():
        data = Database(**yaml.safe_load(HEALTH_YAML_PATH.read_text()))
    else:
        data = Database(results=[], daily_summaries=[])

    queue = []
    for resource in tqdm(bioregistry.resources(), desc="Preparing example URLs"):
        if resource.is_deprecated():
            continue
        example = resource.get_example()
        if example is None:
            continue
        url = bioregistry.get_iri(resource.prefix, example, use_bioregistry_io=False)
        if url is None:
            continue
        queue.append((resource.prefix, example, url))

    import random
    queue = list(random.choices(queue, k=10))

    with logging_redirect_tqdm():
        results = thread_map(_process, queue, desc="Checking providers", unit="prefix")

    failed_percent = sum(result.failed for result in results)
    secho(
        f"{failed_percent}/{len(results)} ({failed_percent / len(results):.2%}) providers failed",
        fg="red",
        bold=True,
    )

    data.results.extend(results)
    data.daily_summaries.append(
        DailySummary(
            date=results[0].date,
            failure_percent=failed_percent,
            total_measured=len(results),
        )
    )

    HEALTH_YAML_PATH.write_text(yaml.safe_dump(data.dict(exclude_none=True)))
    click.echo(f"Wrote to {HEALTH_YAML_PATH}")


def _process(element: Tuple[str, str, str]) -> ProviderStatus:
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
                f'[{datetime.datetime.now().strftime("%H:%M:%S")}] '
                + click.style(prefix, fg="green")
                + " at "
                + click.style(url, fg="red")
                + " failed to download: "
                + click.style(msg, fg="bright_black")
            )
    return ProviderStatus(
        prefix=prefix,
        example=example,
        url=url,
        failed=failed,
        message=msg or None,
        context=context or None,
    )


if __name__ == "__main__":
    main()
