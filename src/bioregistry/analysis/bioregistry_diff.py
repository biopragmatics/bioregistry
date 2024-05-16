import requests
import json
from dateutil.parser import isoparse
from dateutil import tz

# Constants for the GitHub repository information and API URL
GITHUB_API_URL = 'https://api.github.com'
REPO_OWNER = 'tanayshah2'
REPO_NAME = 'bioregistry'
BRANCH = 'main'
FILE_PATH = 'src/bioregistry/data/bioregistry.json'


# Function to get the commit before a given date
def get_commit_before_date(date, owner, name, branch):
    url = f"{GITHUB_API_URL}/repos/{owner}/{name}/commits"
    params = {
        "sha": branch,
        "until": date.isoformat()
    }
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
    params = {
        "ref": commit_sha
    }
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
    updated_prefixes = 0
    for prefix in old_prefixes & new_prefixes:
        if old_data[prefix] != new_data[prefix]:
            updated_prefixes += 1

    return added_prefixes, updated_prefixes


# Main function
def main(date1, date2):
    date1 = isoparse(date1).astimezone(tz.tzutc())
    date2 = isoparse(date2).astimezone(tz.tzutc())

    old_commit = get_commit_before_date(date1, REPO_OWNER, REPO_NAME, BRANCH)
    new_commit = get_commit_before_date(date2, REPO_OWNER, REPO_NAME, BRANCH)

    if not old_commit:
        print(f"Couldn't find commit before {date1}")
        return

    if not new_commit:
        print(f"Couldn't find commit before {date2}")
        return

    old_bioregistry = get_file_at_commit(REPO_OWNER, REPO_NAME, FILE_PATH, old_commit)
    new_bioregistry = get_file_at_commit(REPO_OWNER, REPO_NAME, FILE_PATH, new_commit)

    added, updated = compare_bioregistry(old_bioregistry, new_bioregistry)

    print(f"Added {len(added)} entries, updated {updated} entries")


if __name__ == '__main__':
    date1 = input("Enter the first date (YYYY-MM-DD): ")
    date2 = input("Enter the second date (YYYY-MM-DD): ")
    main(date1, date2)
