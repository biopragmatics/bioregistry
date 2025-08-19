"""Given two dates, analyzes and visualizes changes in the Bioregistry."""

from __future__ import annotations

import datetime
import logging
from typing import Any, NamedTuple, cast

import click
import matplotlib.pyplot as plt
import pandas as pd
import requests
from dateutil import tz
from dateutil.parser import isoparse
from typing_extensions import TypeAlias

logger = logging.getLogger(__name__)

# Constants for the GitHub repository information and API URL
GITHUB_API_URL = "https://api.github.com"
REPO_OWNER = "biopragmatics"
REPO_NAME = "bioregistry"
BRANCH = "main"
FILE_PATH = "src/bioregistry/data/bioregistry.json"


def get_commit_before_date(
    date: datetime.date,
    owner: str = REPO_OWNER,
    name: str = REPO_NAME,
    branch: str = BRANCH,
) -> str | None:
    """Return the last commit before a given date.

    :param date: The date to get the commit before.
    :param owner: The repository owner.
    :param name: The repository name.
    :param branch: The branch name.

    :returns: The SHA of the commit before the given date, or None if no commit is
        found.
    """
    url = f"{GITHUB_API_URL}/repos/{owner}/{name}/commits"
    params = {"sha": branch, "until": date.isoformat()}
    response = requests.get(url, params=params, timeout=15)
    response.raise_for_status()
    commits = response.json()
    if not commits:
        logger.warning(f"No commits found before {date}")
        return None
    first_commit = commits[0]
    if "sha" not in first_commit:
        logger.warning("No 'sha' field found in the first commit.")
        return None
    return cast(str, first_commit["sha"])


BioregistryDataHint: TypeAlias = dict[str, Any]


def get_file_at_commit(
    file_path: str, commit_sha: str, owner: str = REPO_OWNER, name: str = REPO_NAME
) -> BioregistryDataHint:
    """Return the content of a given file at a specific commit.

    :param file_path: The file path in the repository.
    :param commit_sha: The commit SHA.
    :param owner: The repository owner.
    :param name: The repository name.

    :returns: The file content as a dictionary.
    """
    url = f"{GITHUB_API_URL}/repos/{owner}/{name}/contents/{file_path}"
    params = {"ref": commit_sha}
    response = requests.get(url, params=params, timeout=15)
    response.raise_for_status()
    file_info = response.json()
    download_url = file_info["download_url"]
    res = requests.get(download_url, timeout=15)
    res.raise_for_status()
    return cast(BioregistryDataHint, res.json())


ComparsionHint: TypeAlias = dict[str, tuple[Any, Any]]


class CompareBioregistryResult(NamedTuple):
    """A comparison between two different states of the Bioregistry."""

    added_prefixes: set[str]
    deleted_prefixes: set[str]
    updated_prefixes: int
    update_details: list[tuple[str, ComparsionHint]]


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


def compare_entries(old_entry: dict[str, Any], new_entry: dict[str, Any]) -> ComparsionHint:
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
    mapping_keys: set[str] = set()
    for prefix in data:
        if "mappings" in data[prefix]:
            mapping_keys.update(data[prefix]["mappings"].keys())
    return mapping_keys


class DataResult(NamedTuple):
    """Results from comparison between two dates."""

    comparison: CompareBioregistryResult
    old_bioregistry: BioregistryDataHint
    new_bioregistry: BioregistryDataHint
    all_mapping_keys: set[str]


def get_data(old_date_str: str, new_date_str: str) -> DataResult | None:
    """Retrieve and compare bioregistry data between two dates.

    :param old_date_str: The starting date in ISO format.
    :param new_date_str: The ending date in ISO format.

    :returns: Data on added, deleted, and updated prefixes, update details, and old and
        new bioregistry data.
    """
    old_date = isoparse(old_date_str).astimezone(tz.tzutc())
    date2 = isoparse(new_date_str).astimezone(tz.tzutc())

    old_commit = get_commit_before_date(old_date, REPO_OWNER, REPO_NAME, BRANCH)
    new_commit = get_commit_before_date(date2, REPO_OWNER, REPO_NAME, BRANCH)

    if not old_commit:
        logger.error(f"Couldn't find commit before {old_date}")
        return None

    if not new_commit:
        logger.error(f"Couldn't find commit before {date2}")
        return None

    old_bioregistry = get_file_at_commit(FILE_PATH, old_commit, REPO_OWNER, REPO_NAME)
    new_bioregistry = get_file_at_commit(FILE_PATH, new_commit, REPO_OWNER, REPO_NAME)

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
    update_details: list[tuple[str, ComparsionHint]],
    start_date: str,
    end_date: str,
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
                        for mapping_key in mappings.keys():
                            if mapping_key in mapping_fields:
                                mapping_fields[mapping_key] += 1

        # Process other fields, excluding mappings
        for _prefix, changes in update_details:
            for field, _change in changes.items():
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
            plt.title(f"Main Fields Updated from {start_date} to {end_date}")
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
            plt.title(f"Mapping Fields Updated from {start_date} to {end_date}")
            plt.ylabel("Count")
            plt.xlabel("Field")
            plt.xticks(rotation=45, ha="right")
            plt.grid(axis="y", linestyle="--", alpha=0.7)
            plt.tight_layout(pad=3.0)
            plt.show()


@click.command()
@click.argument("date1")
@click.argument("date2")
def compare_dates(date1: str, date2: str) -> None:
    """Process and visualize changes in Bioregistry data between two dates.

    :param date1: The starting date in the format YYYY-MM-DD.
    :param date2: The ending date in the format YYYY-MM-DD.
    """
    data = get_data(date1, date2)
    if data is not None:
        summarize_changes(data.comparison)
        visualize_changes(data.comparison.update_details, date1, date2, data.all_mapping_keys)


if __name__ == "__main__":
    compare_dates()
