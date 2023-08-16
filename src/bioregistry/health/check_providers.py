# -*- coding: utf-8 -*-

"""A script to check which providers in entries in the Bioregistry actually can be accessed."""

import datetime
from operator import attrgetter
from typing import List, NamedTuple, Optional

import click
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
    status_code: Optional[int]
    failed: bool
    exception: Optional[str]
    context: Optional[str]


class Summary(BaseModel):
    """Statistics for a single run."""

    total_measured: int
    total_failed: int
    total_success: int
    failure_percent: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="The percentage of providers that did not successfully ping.",
    )


class Delta(BaseModel):
    """Change between runs."""

    new: List[str] = Field(
        description="Prefixes that are new in the current run that were not present in the previous run"
    )
    forgotten: List[str] = Field(
        description="Prefixes that were checked in the previous run but not the current run"
    )
    revived: List[str] = Field(
        description="Prefixes that failed in the previous run but are now passing the current run"
    )
    fallen: List[str] = Field(
        description="Prefixes that were passing in the previous run but are now failing in the current run"
    )
    intersection: int = Field(description="Size of intersection")
    alive: int = Field(description="Prefixes that passed in the previous and this run")
    dead: int = Field(description="Prefixes failed in the previous and this run")


class Run(BaseModel):
    """Results and metadata about a single provider check run."""

    time: datetime.datetime = Field(default_factory=datetime.datetime.now)
    date: str = Field(default_factory=lambda: datetime.datetime.now().strftime("%Y-%m-%d"))
    results: List[ProviderStatus]
    summary: Summary
    delta: Optional[Delta] = Field(description="Information about the changes since the last run")


class Database(BaseModel):
    """A database of runs of the provider check."""

    runs: List[Run] = Field(default_factory=list)


class QueueTuple(NamedTuple):
    """A tuple representing an input to the provider check."""

    prefix: str
    example: str
    url: str


@click.command()
def main() -> None:
    """Run the provider health check script."""
    if HEALTH_YAML_PATH.is_file():
        database = Database(**yaml.safe_load(HEALTH_YAML_PATH.read_text()))
    else:
        click.secho(f"Creating new database at {HEALTH_YAML_PATH}", fg="green")
        database = Database()

    queue: List[QueueTuple] = []

    # this is very fast and does not require tqdm
    for resource in bioregistry.resources():
        if resource.is_deprecated():
            continue
        example = resource.get_example()
        if example is None:
            continue
        url = bioregistry.get_iri(resource.prefix, example, use_bioregistry_io=False)
        if url is None:
            continue
        queue.append(QueueTuple(resource.prefix, example, url))

    with logging_redirect_tqdm():
        results = thread_map(_process, queue, desc="Checking providers", unit="prefix")

    total = len(results)
    total_failed = sum(result.failed for result in results)
    failure_percent = total_failed / total
    secho(
        f"{total_failed:,}/{total:,} ({failure_percent:.1%}) providers failed",
        fg="red",
        bold=True,
    )

    # TODO smooth delta against last N runs, since some things sporadically
    #  come in and out
    delta = (
        _calculate_delta(results, max(database.runs, key=attrgetter("time")).results)
        if database.runs
        else None
    )
    current_run = Run(
        results=results,
        summary=Summary(
            total_measured=total,
            total_failed=total_failed,
            total_success=total - total_failed,
            failure_percent=round(100 * failure_percent, 1),
        ),
        delta=delta,
    )
    database.runs.append(current_run)
    database.runs = sorted(database.runs, key=attrgetter("time"), reverse=True)

    HEALTH_YAML_PATH.write_text(yaml.safe_dump(database.dict(exclude_none=True)))
    click.echo(f"Wrote to {HEALTH_YAML_PATH}")


def _calculate_delta(current: List[ProviderStatus], previous: List[ProviderStatus]) -> Delta:
    current_results = {status.prefix: status.failed for status in current}
    previous_results = {status.prefix: status.failed for status in previous}
    new = set(current_results).difference(previous_results)
    forgotten = set(previous_results).difference(current_results)
    intersection_prefixes = set(current_results).intersection(previous_results)
    fallen = {
        prefix
        for prefix in intersection_prefixes
        if not previous_results[prefix] and current_results[prefix]
    }
    revived = {
        prefix
        for prefix in intersection_prefixes
        if previous_results[prefix] and not current_results[prefix]
    }
    alive = sum(
        not previous_results[prefix] and not current_results[prefix]
        for prefix in intersection_prefixes
    )
    dead = sum(
        previous_results[prefix] and current_results[prefix] for prefix in intersection_prefixes
    )
    return Delta(
        new=sorted(new),
        fallen=sorted(fallen),
        revived=sorted(revived),
        forgotten=sorted(forgotten),
        intersection=len(intersection_prefixes),
        alive=alive,
        dead=dead,
    )


def _process(element: QueueTuple) -> ProviderStatus:
    prefix, example, url = element

    status_code: Optional[int]
    exception: Optional[str]
    context: Optional[str]

    try:
        res = requests.head(url, timeout=10, allow_redirects=True)
    except IOError as e:
        status_code = None
        failed = True
        exception = e.__class__.__name__
        context = str(e)
    else:
        status_code = res.status_code
        failed = res.status_code != 200
        exception = None
        context = None

    if failed:
        text = (
            f'[{datetime.datetime.now().strftime("%H:%M:%S")}] '
            + click.style(prefix, fg="green")
            + " at "
            + click.style(url, fg="red")
            + " failed to download"
        )
        if exception:
            text += ": " + click.style(exception, fg="bright_black")
        with tqdm.external_write_mode():
            click.echo(text)

    return ProviderStatus(
        prefix=prefix,
        example=example,
        url=url,
        failed=failed,
        status_code=status_code,
        exception=exception,
        context=context,
    )


if __name__ == "__main__":
    main()
