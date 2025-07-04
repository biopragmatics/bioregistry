"""Update the bioregistry from GitHub Issue templates."""

from __future__ import annotations

import itertools as itt
import logging
import os
from collections.abc import Iterable, Mapping
from subprocess import CalledProcessError, check_output
from typing import Any, cast

import more_itertools
import pystow
import requests

logger = logging.getLogger(__name__)
HERE = os.path.dirname(os.path.abspath(__file__))
MAIN_BRANCH = "main"


def has_token() -> bool:
    """Check if there is a GitHub token available."""
    return pystow.get_config("github", "token") is not None


def get_issues_with_pr(issue_ids: Iterable[int], token: str | None = None) -> set[int]:
    """Get the set of issues that are already closed by a pull request."""
    pulls = list_pulls(owner="bioregistry", repo="bioregistry", token=token)
    return {
        issue_id
        for pull, issue_id in itt.product(pulls, issue_ids)
        if f"Closes #{issue_id}" in (pull.get("body") or "")
    }


def get_headers(token: str | None = None) -> dict[str, str]:
    """Get GitHub headers."""
    headers = {
        "Accept": "application/vnd.github.v3+json",
    }
    token = pystow.get_config("github", "token", passthrough=token)
    if token:
        headers["Authorization"] = f"token {token}"
    return headers


def requests_get(
    path: str, token: str | None = None, params: Mapping[str, Any] | None = None
) -> Any:
    """Send a get request to the GitHub API."""
    path = path.lstrip("/")
    return requests.get(
        f"https://api.github.com/{path}",
        headers=get_headers(token=token),
        params=params,
        timeout=15,
    ).json()


def list_pulls(
    *,
    owner: str,
    repo: str,
    token: str | None = None,
) -> list[dict[str, Any]]:
    """List pull requests.

    :param owner: The name of the owner/organization for the repository.
    :param repo: The name of the repository.
    :param token: The GitHub OAuth token. Not required, but if given, will let you make
        many more queries before getting rate limited.

    :returns: JSON response from GitHub
    """
    return cast(list[dict[str, Any]], requests_get(f"repos/{owner}/{repo}/pulls", token=token))


def open_bioregistry_pull_request(
    *,
    title: str,
    head: str,
    body: str | None = None,
    token: str | None = None,
) -> dict[str, Any]:
    """Open a pull request to the Bioregistry via :func:`open_pull_request`."""
    return open_pull_request(
        owner="bioregistry",
        repo="bioregistry",
        base=MAIN_BRANCH,
        title=title,
        head=head,
        body=body,
        token=token,
    )


def open_pull_request(
    *,
    owner: str,
    repo: str,
    title: str,
    head: str,
    base: str,
    body: str | None = None,
    token: str | None = None,
) -> dict[str, Any]:
    """Open a pull request.

    :param owner: The name of the owner/organization for the repository.
    :param repo: The name of the repository.
    :param title: name of the PR
    :param head: name of the source branch
    :param base: name of the target branch
    :param body: body of the PR (optional)
    :param token: The GitHub OAuth token. Not required, but if given, will let you make
        many more queries before getting rate limited.

    :returns: JSON response from GitHub
    """
    data = {
        "title": title,
        "head": head,
        "base": base,
    }
    if body:
        data["body"] = body
    res = requests.post(
        f"https://api.github.com/repos/{owner}/{repo}/pulls",
        headers=get_headers(token=token),
        json=data,
        timeout=15,
    )
    return res.json()  # type:ignore


def get_bioregistry_form_data(
    labels: Iterable[str],
    token: str | None = None,
    remapping: Mapping[str, str] | None = None,
) -> Mapping[int, dict[str, str]]:
    """Get parsed form data from issues on the Bioregistry matching the given labels via :func:get_form_data`.

    :param labels: Labels to match
    :param token: The GitHub OAuth token. Not required, but if given, will let you make
        many more queries before getting rate limited.
    :param remapping: A dictionary for mapping the headers of the form into new values.
        This is useful since the headers themselves will be human readable text, and not
        nice keys for JSON data

    :returns: A mapping from github issue issue data
    """
    return get_form_data(
        owner="bioregistry", repo="bioregistry", labels=labels, token=token, remapping=remapping
    )


def get_form_data(
    owner: str,
    repo: str,
    labels: Iterable[str],
    token: str | None = None,
    remapping: Mapping[str, str] | None = None,
) -> Mapping[int, dict[str, str]]:
    """Get parsed form data from issues matching the given labels.

    :param owner: The name of the owner/organization for the repository.
    :param repo: The name of the repository.
    :param labels: Labels to match
    :param token: The GitHub OAuth token. Not required, but if given, will let you make
        many more queries before getting rate limited.
    :param remapping: A dictionary for mapping the headers of the form into new values.
        This is useful since the headers themselves will be human readable text, and not
        nice keys for JSON data

    :returns: A mapping from github issue issue data
    """
    labels = labels if isinstance(labels, str) else ",".join(labels)
    res_json = requests_get(
        f"repos/{owner}/{repo}/issues",
        token=token,
        params={
            "labels": labels,
            "state": "open",
        },
    )
    rv = {
        issue["number"]: parse_body(issue["body"])
        for issue in res_json
        if "pull_request" not in issue
    }
    if remapping:
        rv = {issue: remap(body_data, remapping) for issue, body_data in rv.items()}
    return rv


def get_form_data_for_issue(
    owner: str,
    repo: str,
    issue: int,
    token: str | None = None,
    remapping: Mapping[str, str] | None = None,
) -> dict[str, str]:
    """Get parsed form data from an issue.

    :param owner: The name of the owner/organization for the repository.
    :param repo: The name of the repository.
    :param issue: The issue number
    :param token: The GitHub OAuth token. Not required, but if given, will let you make
        many more queries before getting rate limited.
    :param remapping: A dictionary for mapping the headers of the form into new values.
        This is useful since the headers themselves will be human readable text, and not
        nice keys for JSON data

    :returns: A mapping from github issue issue data
    """
    res_json = requests_get(f"repos/{owner}/{repo}/issues/{issue}", token=token)
    data = parse_body(res_json["body"])
    if remapping:
        return remap(data, remapping)
    else:
        return data


def remap(data: dict[str, Any], mapping: Mapping[str, str]) -> dict[str, Any]:
    """Map the keys in dictionary ``d`` based on dictionary ``m``."""
    try:
        return {mapping[key]: value for key, value in data.items()}
    except KeyError:
        logger.warning("original dict: %s", data)
        logger.warning("mapping dict: %s", mapping)
        raise


def parse_body(body: str) -> dict[str, Any]:
    """Parse the body string from a GitHub issue (via the API).

    :param body: The body string from a GitHub issue (via the API) that corresponds to a
        form

    :returns: A dictionary of keys (headers) to values
    """
    rv = {}
    lines = [line.strip() for line in body.splitlines() if line.strip()]
    for group in more_itertools.split_before(lines, lambda line: line.startswith("### ")):
        header, *rest = group
        header = header.lstrip("#").lstrip()
        rest_str = " ".join(x.strip() for x in rest)
        if rest_str == "_No response_" or not rest_str:
            continue
        rv[header] = rest_str
    return rv


def status_porcelain() -> str | None:
    """Return if the current directory has any uncommitted stuff."""
    return _git("status", "--porcelain")


def push(*args: str) -> str | None:
    """Push the git repo."""
    return _git("push", *args)


def branch(name: str) -> str | None:
    """Create a new branch and switch to it.

    :param name: The name of the new branch

    :returns: The message from the command

    .. seealso::

        https://git-scm.com/book/en/v2/Git-Branching-Basic-Branching-and-Merging
    """
    return _git("checkout", "-b", name)


def home() -> str | None:
    """Return to the main branch.

    :returns: The message from the command
    """
    return _git("checkout", MAIN_BRANCH)


def commit(message: str, *args: str) -> str | None:
    """Make a commit with the following message."""
    return _git("commit", *args, "-m", message)


def commit_all(message: str) -> str | None:
    """Make a commit with the following message.

    :param message: The message to go with the commit.

    :returns: The message from the command

    .. note::

        ``-a`` means "commit all files"
    """
    return _git("commit", "-m", message, "-a")


def _git(*args: str) -> str | None:
    with open(os.devnull, "w") as devnull:
        try:
            ret = check_output(  # noqa: S603
                ["git", *args],  # noqa:S607
                cwd=os.path.dirname(__file__),
                stderr=devnull,
            )
        except CalledProcessError as e:
            logger.warning(f"error in _git:\n{e}")
            return None
        else:
            return ret.strip().decode("utf-8")
