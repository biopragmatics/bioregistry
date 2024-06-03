import requests
import json
import click
import pandas as pd
import matplotlib.pyplot as plt
from dateutil.parser import isoparse
from dateutil import tz

# Constants for the GitHub repository information and API URL
GITHUB_API_URL = "https://api.github.com"
REPO_OWNER = "biopragmatics"
REPO_NAME = "bioregistry"
BRANCH = "main"
FILE_PATH = "src/bioregistry/data/bioregistry.json"


# Function to get the commit before a given date
def get_commit_before_date(date, owner, name, branch):
    url = f"{GITHUB_API_URL}/repos/{owner}/{name}/commits"
    params = {"sha": branch, "until": date.isoformat()}
    response = requests.get(url, params=params)
    response.raise_for_status()
    commits = response.json()
    if commits:
        first_commit = commits[0]
        if "sha" in first_commit:
            return first_commit["sha"]
        else:
            print("No 'sha' field found in the first commit.")
    else:
        print(f"No commits found before {date}")
    return None


# Function to get the file content at a specific commit
def get_file_at_commit(owner, name, file_path, commit_sha):
    url = f"{GITHUB_API_URL}/repos/{owner}/{name}/contents/{file_path}"
    params = {"ref": commit_sha}
    response = requests.get(url, params=params)
    response.raise_for_status()
    file_info = response.json()
    download_url = file_info["download_url"]
    file_content_response = requests.get(download_url)
    file_content_response.raise_for_status()
    return json.loads(file_content_response.text)


# Function to compare two versions of the bioregistry data
def compare_bioregistry(old_data, new_data):
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

    return added_prefixes, deleted_prefixes, updated_prefixes, update_details
    return added_prefixes, deleted_prefixes, updated_prefixes, update_details


# Function to compare individual entries for detailed changes
def compare_entries(old_entry, new_entry):
    changes = {}
    for key in old_entry.keys() | new_entry.keys():
        if old_entry.get(key) != new_entry.get(key):
            changes[key] = (old_entry.get(key), new_entry.get(key))
    return changes


def get_all_mapping_keys(data):
    mapping_keys = set()
    for prefix in data:
        if "mappings" in data[prefix]:
            mapping_keys.update(data[prefix]["mappings"].keys())
    return mapping_keys


def get_data(date1, date2):
    date1 = isoparse(date1).astimezone(tz.tzutc())
    date2 = isoparse(date2).astimezone(tz.tzutc())

    old_commit = get_commit_before_date(date1, REPO_OWNER, REPO_NAME, BRANCH)
    new_commit = get_commit_before_date(date2, REPO_OWNER, REPO_NAME, BRANCH)

    if not old_commit:
        print(f"Couldn't find commit before {date1}")
        return None, None, None, None, None

    if not new_commit:
        print(f"Couldn't find commit before {date2}")
        return None, None, None, None, None

    old_bioregistry = get_file_at_commit(REPO_OWNER, REPO_NAME, FILE_PATH, old_commit)
    new_bioregistry = get_file_at_commit(REPO_OWNER, REPO_NAME, FILE_PATH, new_commit)

    added, deleted, updated, update_details = compare_bioregistry(old_bioregistry, new_bioregistry)

    old_mapping_keys = get_all_mapping_keys(old_bioregistry)
    new_mapping_keys = get_all_mapping_keys(new_bioregistry)
    all_mapping_keys = old_mapping_keys.union(new_mapping_keys)

    return (
        added,
        deleted,
        updated,
        update_details,
        old_bioregistry,
        new_bioregistry,
        all_mapping_keys,
    )


def summarize_changes(added, deleted, updated, update_details):
    print(f"Total Added Prefixes: {len(added)}")
    print(f"Total Deleted Prefixes: {len(deleted)}")
    print(f"Total Updated Prefixes: {updated}")


def visualize_changes(
    added, deleted, updated, update_details, start_date, end_date, all_mapping_keys
):
    main_fields = {}
    mapping_fields = {key: 0 for key in all_mapping_keys}

    if update_details:
        # Process mappings fields to exclude them
        for changes in update_details:
            for field, change in changes.items():
                if field == "mappings":
                    mappings = change[1] if isinstance(change[1], dict) else change[0]
                    if mappings:
                        for mapping_key in mappings.keys():
                            if mapping_key in mapping_fields:
                                mapping_fields[mapping_key] += 1

        # Process other fields, excluding mappings
        for changes in update_details:
            for field in changes.items():
                # print(f"Prefix: {prefix}, Field: {field}, Change: {change}")
                if field in mapping_fields or field == "mappings":
                    # print(f"Skipping field: {field}")
                    continue
                if field == "contributor" or field == "contributor_extras":
                    continue
                if field in main_fields:
                    main_fields[field] += 1
                else:
                    main_fields[field] = 1

        # # Debug output for main fields and mapping fields
        # print("\nMain Fields:")
        # for field, count in main_fields.items():
        #     print(f"{field}: {count}")
        #
        # print("\nMapping Fields:")
        # for field, count in mapping_fields.items():
        #     print(f"{field}: {count}")

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
def final(date1, date2):
    """
        This function processes and visualizes changes in Bioregistry data between two dates.

        Args:
            date1 (str): The starting date in the format YYYY-MM-DD.
            date2 (str): The ending date in the format YYYY-MM-DD.

        Returns:
            None
        """
    added, deleted, updated, update_details, old_data, new_data, all_mapping_keys = get_data(
        date1, date2
    )
    if added is not None and updated is not None:
        summarize_changes(added, deleted, updated, update_details)
        visualize_changes(added, deleted, updated, update_details, date1, date2, all_mapping_keys)


if __name__ == "__main__":
    final()
