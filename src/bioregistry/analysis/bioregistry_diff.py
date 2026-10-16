"""Given two dates, analyzes and visualizes changes in the Bioregistry."""

from __future__ import annotations

import datetime
import json
import logging
import typing
from pathlib import PurePath
from typing import Any, Literal, NamedTuple, TypeAlias, cast

import click
import matplotlib.pyplot as plt
import pandas as pd
import requests
from pystow.git import get_commit_hash_before, get_current_commit_hash, show

from bioregistry.constants import HERE

logger = logging.getLogger(__name__)

# Constants for the GitHub repository information and API URL
GITHUB_API_URL = "https://api.github.com"
REPO_OWNER = "biopragmatics"
REPO_NAME = "bioregistry"
BRANCH = "main"
FILE_PATH = "src/bioregistry/data/bioregistry.json"

Method = Literal["github", "local"]


def get_commit_before_date(
    date: datetime.date,
    owner: str | None = None,
    name: str | None = None,
    branch: str | None = None,
) -> str:
    """Return the last commit before a given date.

    :param date: The date to get the commit before.
    :param owner: The repository owner.
    :param name: The repository name.
    :param branch: The branch name.

    :returns: The SHA of the commit before the given date, or None if no commit is
        found.
    """
    if owner is None:
        owner = REPO_OWNER
    if name is None:
        name = REPO_NAME
    if branch is None:
        branch = BRANCH
    url = f"{GITHUB_API_URL}/repos/{owner}/{name}/commits"
    params = {"sha": branch, "until": date.isoformat()}
    response = requests.get(url, params=params, timeout=15)
    response.raise_for_status()
    commits = response.json()
    if not commits:
        raise ValueError(f"No commits found before {date}")
    first_commit = commits[0]
    if "sha" not in first_commit:
        raise ValueError("No 'sha' field found in the first commit.")
    return cast(str, first_commit["sha"])


BioregistryDataHint: TypeAlias = dict[str, Any]


def get_file_at_commit(
    path: str | PurePath,
    commit_hash: str,
    *,
    owner: str | None = None,
    name: str | None = None,
    method: Method = "local",
) -> BioregistryDataHint:
    """Return the content of a given file at a specific commit.

    :param path: The file path in the repository.
    :param commit_hash: The commit hash.
    :param owner: The repository owner.
    :param name: The repository name.
    :param method: The method to use, either local lookup or GitHub

    :returns: The file content as a dictionary.
    """
    if method == "github":
        if owner is None:
            owner = REPO_OWNER
        if name is None:
            name = REPO_NAME
        url = f"{GITHUB_API_URL}/repos/{owner}/{name}/contents/{path}"
        params = {"ref": commit_hash}
        contents_res = requests.get(url, params=params, timeout=15)
        contents_res.raise_for_status()
        file_info = contents_res.json()
        download_url = file_info["download_url"]
        registry_res = requests.get(download_url, timeout=15)
        registry_res.raise_for_status()
        rv = registry_res.json()
    elif method == "local":
        rv = json.loads(show(HERE, commit_hash, path))
    else:
        raise ValueError
    return cast(BioregistryDataHint, rv)


ComparisonHint: TypeAlias = dict[str, tuple[Any, Any]]


class CompareBioregistryResult(NamedTuple):
    """A comparison between two different states of the Bioregistry."""

    added_prefixes: set[str]
    deleted_prefixes: set[str]
    updated_prefixes: int
    update_details: list[tuple[str, ComparisonHint]]


def compare_bioregistry(
    old_data: dict[str, dict[str, Any]], new_data: dict[str, dict[str, Any]]
) -> CompareBioregistryResult:
    """Return comparison of two versions of the bioregistry data.

    :param old_data: The old bioregistry data.
    :param new_data: The new bioregistry data.

    :returns: Sets of added prefixes, deleted prefixes, and a count of updated prefixes,
        along with update details.
    """
    old_prefixes = set(old_data.keys())
    new_prefixes = set(new_data.keys())

    added_prefixes = new_prefixes - old_prefixes
    deleted_prefixes = old_prefixes - new_prefixes
    updated_prefixes = 0
    update_details = []

    for prefix in old_prefixes & new_prefixes:
        if old_data[prefix] != new_data[prefix]:
            updated_prefixes += 1
            changes = compare_entries(old_data[prefix], new_data[prefix])
            update_details.append((prefix, changes))

    return CompareBioregistryResult(
        added_prefixes, deleted_prefixes, updated_prefixes, update_details
    )


def compare_entries(old_entry: dict[str, Any], new_entry: dict[str, Any]) -> ComparisonHint:
    """Return detailed changes within individual entries.

    :param old_entry: The old entry data.
    :param new_entry: The new entry data.

    :returns: A dictionary of changes.
    """
    changes = {}
    for key in old_entry.keys() | new_entry.keys():
        if old_entry.get(key) != new_entry.get(key):
            changes[key] = (old_entry.get(key), new_entry.get(key))
    return changes


def get_all_mapping_keys(data: dict[str, dict[str, Any]]) -> set[str]:
    """Return all unique mapping keys from the bioregistry data.

    :param data: The bioregistry data.

    :returns: A set of all unique mapping keys.
    """
    return {
        key
        for subdata in data.values()
        if (mappings := subdata.get("mappings"))
        for key in mappings
    }


class DataResult(NamedTuple):
    """Results from comparison between two dates."""

    comparison: CompareBioregistryResult
    old_bioregistry: BioregistryDataHint
    new_bioregistry: BioregistryDataHint
    all_mapping_keys: set[str]


def compare_commits(
    start_commit: str, end_commit: str, *, owner: str | None = None, name: str | None = None
) -> DataResult:
    """Compare two commits."""
    old_bioregistry = get_file_at_commit(FILE_PATH, start_commit, owner=owner, name=name)
    new_bioregistry = get_file_at_commit(FILE_PATH, end_commit, owner=owner, name=name)

    compare_bioregistry_rv = compare_bioregistry(old_bioregistry, new_bioregistry)

    old_mapping_keys = get_all_mapping_keys(old_bioregistry)
    new_mapping_keys = get_all_mapping_keys(new_bioregistry)
    all_mapping_keys = old_mapping_keys.union(new_mapping_keys)

    return DataResult(compare_bioregistry_rv, old_bioregistry, new_bioregistry, all_mapping_keys)


def summarize_changes(comparison: CompareBioregistryResult) -> None:
    """Log a summary of changes in the bioregistry data."""
    logger.info(f"Total Added Prefixes: {len(comparison.added_prefixes)}")
    logger.info(f"Total Deleted Prefixes: {len(comparison.deleted_prefixes)}")
    logger.info(f"Total Updated Prefixes: {comparison.updated_prefixes}")


def visualize_changes(
    update_details: list[tuple[str, ComparisonHint]],
    start_date: datetime.date,
    end_date: datetime.date,
    all_mapping_keys: set[str],
) -> None:
    """Display plots of changes in the bioregistry data.

    :param update_details: List of update details.
    :param start_date: The starting date.
    :param end_date: The ending date.
    :param all_mapping_keys: Set of all mapping keys.
    """
    main_fields: dict[str, int] = {}
    mapping_fields = dict.fromkeys(all_mapping_keys, 0)

    if update_details:
        # Process mappings fields to exclude them
        for _prefix, changes in update_details:
            for field, change in changes.items():
                if field == "mappings":
                    mappings = change[1] if isinstance(change[1], dict) else change[0]
                    if mappings:
                        for mapping_key in mappings:
                            if mapping_key in mapping_fields:
                                mapping_fields[mapping_key] += 1

        # Process other fields, excluding mappings
        for _prefix, changes in update_details:
            for field in changes:
                if field in mapping_fields or field == "mappings":
                    continue
                if field == "contributor" or field == "contributor_extras":
                    continue
                if field in main_fields:
                    main_fields[field] += 1
                else:
                    main_fields[field] = 1

        # Plot for main fields
        if main_fields:
            main_fields_df = pd.DataFrame(list(main_fields.items()), columns=["Field", "Count"])
            main_fields_df = main_fields_df.sort_values(by="Count", ascending=False)

            plt.figure(figsize=(15, 8))
            plt.bar(main_fields_df["Field"], main_fields_df["Count"], color="green")
            plt.title(
                f"Main Fields Updated from {start_date.isoformat()} to {end_date.isoformat()}"
            )
            plt.ylabel("Count")
            plt.xlabel("Field")
            plt.xticks(rotation=45, ha="right")
            plt.grid(axis="y", linestyle="--", alpha=0.7)
            plt.tight_layout(pad=3.0)
            plt.show()

        # Plot for mapping fields
        if mapping_fields:
            mapping_fields_df = pd.DataFrame(
                list(mapping_fields.items()), columns=["Field", "Count"]
            )
            mapping_fields_df = mapping_fields_df.sort_values(by="Count", ascending=False)

            plt.figure(figsize=(15, 8))
            plt.bar(mapping_fields_df["Field"], mapping_fields_df["Count"], color="blue")
            plt.title(
                f"Mapping Fields Updated from {start_date.isoformat()} to {end_date.isoformat()}"
            )
            plt.ylabel("Count")
            plt.xlabel("Field")
            plt.xticks(rotation=45, ha="right")
            plt.grid(axis="y", linestyle="--", alpha=0.7)
            plt.tight_layout(pad=3.0)
            plt.show()


@click.command()
@click.option("--start-date", help="the starting date")
@click.option("--days-ago", help="number of days ago", type=int)
@click.option("--end-date", help="The optional ending date for comparison, defaults to today")
@click.option("--method", type=click.Choice(typing.get_args(Method)), default="local")
def compare_dates(
    days_ago: int | None, start_date: str | None, end_date: str | None, method: Method
) -> None:
    """Process and visualize changes in Bioregistry data between two dates."""
    if end_date is None:
        end_date_ = datetime.date.today()
        end_hash = get_current_commit_hash(HERE)
    else:
        end_date_ = datetime.date.fromisoformat(end_date)
        end_hash = get_commit_before_date(end_date_)

    if days_ago is not None:
        start_date_ = end_date_ + datetime.timedelta(days=days_ago)
        if method == "github":
            start_hash = get_commit_before_date(start_date_)
        else:
            start_hash = get_commit_hash_before(HERE, f"{days_ago} days ago")
    elif start_date is not None:
        start_date_ = datetime.date.fromisoformat(start_date)
        start_hash = get_commit_before_date(start_date_)
    else:
        raise click.ClickException("Must specify either --start-date or --days-ago")

    click.echo(f"comparing from {start_date_} to {end_date_}")
    data = compare_commits(start_hash, end_hash)
    if data is None:
        raise click.ClickException("No data")
    summarize_changes(data.comparison)
    visualize_changes(data.comparison.update_details, start_date_, end_date_, data.all_mapping_keys)


if __name__ == "__main__":
    compare_dates()
