# -*- coding: utf-8 -*-

"""Update the bioregistry from GitHub Issue templates."""

import itertools as itt
import logging
import os
from subprocess import CalledProcessError, check_output  # noqa: S404
from typing import Any, Dict, Iterable, Mapping, Optional, Set

import more_itertools
import pystow
import requests

logger = logging.getLogger(__name__)
HERE = os.path.dirname(os.path.abspath(__file__))
MAIN_BRANCH = "main"


def has_token() -> bool:
    """Check if there is a github token available."""
    return pystow.get_config("github", "token") is not None


def get_issues_with_pr(issue_ids: Iterable[int], token: Optional[str] = None) -> Set[int]:
    """Get the set of issues that are already closed by a pull request."""
    pulls = list_pulls(owner="bioregistry", repo="bioregistry", token=token)
    return {
        issue_id
        for pull, issue_id in itt.product(pulls, issue_ids)
        if f"Closes #{issue_id}" in pull.get("body", "")
    }


def get_headers(token: Optional[str] = None):
    """Get github headers."""
    headers = {
        "Accept": "application/vnd.github.v3+json",
    }
    token = pystow.get_config("github", "token", passthrough=token)
    if token:
        headers["Authorization"] = f"token {token}"
    return headers


def list_pulls(
    *,
    owner: str,
    repo: str,
    token: Optional[str] = None,
):
    """List pull requests.

    :param owner: The name of the owner/organization for the repository.
    :param repo: The name of the repository.
    :param token: The GitHub OAuth token. Not required, but if given, will let
        you make many more queries before getting rate limited.
    :returns: JSON response from GitHub
    """
    return requests.get(
        f"https://api.github.com/repos/{owner}/{repo}/pulls",
        headers=get_headers(token=token),
    ).json()


def open_bioregistry_pull_request(
    *,
    title: str,
    head: str,
    body: Optional[str] = None,
    token: Optional[str] = None,
):
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
    body: Optional[str] = None,
    token: Optional[str] = None,
):
    """Open a pull request.

    :param owner: The name of the owner/organization for the repository.
    :param repo: The name of the repository.
    :param title: name of the PR
    :param head: name of the source branch
    :param base: name of the target branch
    :param body: body of the PR (optional)
    :param token: The GitHub OAuth token. Not required, but if given, will let
        you make many more queries before getting rate limited.
    :returns: JSON response from GitHub
    """
    data = {
        "title": title,
        "head": head,
        "base": base,
    }
    if body:
        data["body"] = body
    return requests.post(
        f"https://api.github.com/repos/{owner}/{repo}/pulls",
        headers=get_headers(token=token),
        json=data,
    ).json()


def get_bioregistry_form_data(
    labels: Iterable[str],
    token: Optional[str] = None,
    remapping: Optional[Mapping[str, str]] = None,
) -> Mapping[int, Dict[str, str]]:
    """Get parsed form data from issues on the Bioregistry matching the given labels via :func:get_form_data`.

    :param labels: Labels to match
    :param token: The GitHub OAuth token. Not required, but if given, will let
        you make many more queries before getting rate limited.
    :param remapping: A dictionary for mapping the headers of the form into new values. This is useful since
        the headers themselves will be human readable text, and not nice keys for JSON data
    :return: A mapping from github issue issue data
    """
    return get_form_data(
        owner="bioregistry", repo="bioregistry", labels=labels, token=token, remapping=remapping
    )


def get_form_data(
    owner: str,
    repo: str,
    labels: Iterable[str],
    token: Optional[str] = None,
    remapping: Optional[Mapping[str, str]] = None,
) -> Mapping[int, Dict[str, str]]:
    """Get parsed form data from issues matching the given labels.

    :param owner: The name of the owner/organization for the repository.
    :param repo: The name of the repository.
    :param labels: Labels to match
    :param token: The GitHub OAuth token. Not required, but if given, will let
        you make many more queries before getting rate limited.
    :param remapping: A dictionary for mapping the headers of the form into new values. This is useful since
        the headers themselves will be human readable text, and not nice keys for JSON data
    :return: A mapping from github issue issue data
    """
    labels = labels if isinstance(labels, str) else ",".join(labels)
    res = requests.get(
        f"https://api.github.com/repos/{owner}/{repo}/issues",
        headers=get_headers(token=token),
        params={
            "labels": labels,
            "state": "open",
        },
    )
    rv = {
        issue["number"]: parse_body(issue["body"])
        for issue in res.json()
        if "pull_request" not in issue
    }
    if remapping:
        rv = {issue: remap(body_data, remapping) for issue, body_data in rv.items()}
    return rv


def remap(data: Dict[str, Any], mapping: Mapping[str, str]) -> Dict[str, Any]:
    """Map the keys in dictionary ``d`` based on dictionary ``m``."""
    try:
        return {mapping[key]: value for key, value in data.items()}
    except KeyError:
        logger.warning("original dict: %s", data)
        logger.warning("mapping dict: %s", mapping)
        raise


def parse_body(body: str) -> Dict[str, Any]:
    """Parse the body string from a GitHub issue (via the API).

    :param body: The body string from a GitHub issue (via the API) that corresponds to a form
    :returns: A dictionary of keys (headers) to values
    """
    rv = {}
    lines = [line.strip() for line in body.splitlines() if line.strip()]
    for group in more_itertools.split_before(lines, lambda line: line.startswith("### ")):
        header, *rest = group
        header = header.lstrip("#").lstrip()
        rest = " ".join(x.strip() for x in rest)
        if rest == "_No response_" or not rest:
            continue
        rv[header] = rest
    return rv


def status_porcelain() -> Optional[str]:
    """Return if the current directory has any uncommitted stuff."""
    return _git("status", "--porcelain")


def push(*args) -> Optional[str]:
    """Push the git repo."""
    return _git("push", *args)


def branch(name: str) -> Optional[str]:
    """Create a new branch and switch to it.

    :param name: The name of the new branch
    :returns: The message from the command

    .. seealso:: https://git-scm.com/book/en/v2/Git-Branching-Basic-Branching-and-Merging
    """
    return _git("checkout", "-b", name)


def home() -> Optional[str]:
    """Return to the main branch.

    :returns: The message from the command
    """
    return _git("checkout", MAIN_BRANCH)


def commit(message: str, *args: str) -> Optional[str]:
    """Make a commit with the following message."""
    return _git("commit", *args, "-m", message)


def commit_all(message: str) -> Optional[str]:
    """Make a commit with the following message.

    :param message: The message to go with the commit.
    :returns: The message from the command

    .. note:: ``-a`` means "commit all files"
    """
    return _git("commit", "-m", message, "-a")


def _git(*args: str) -> Optional[str]:
    with open(os.devnull, "w") as devnull:
        try:
            ret = check_output(  # noqa: S603,S607
                ["git", *args],
                cwd=os.path.dirname(__file__),
                stderr=devnull,
            )
        except CalledProcessError as e:
            logger.warning(f"error in _git:\n{e}")
            return None
        else:
            return ret.strip().decode("utf-8")
