# -*- coding: utf-8 -*-

"""Update the bioregistry from GitHub Issue templates."""

import logging
import os
import sys
import time
from subprocess import CalledProcessError, check_output  # noqa: S404
from typing import Any, Dict, Iterable, Mapping, Optional, Tuple
from uuid import uuid4

import click
import more_itertools
import pystow
import requests
from more_click import verbose_option
from rich import print

import bioregistry
from bioregistry.constants import BIOREGISTRY_PATH
from bioregistry.schema import Resource
from bioregistry.utils import add_resource

logger = logging.getLogger(__name__)
TOKEN = pystow.get_config("github", "access_token")
HERE = os.path.dirname(os.path.abspath(__file__))
MAIN_BRANCH = "main"
#: A mapping from the headers in the GitHub new prefix form to Bioregistry internal keys
MAPPING = {
    "Prefix": "prefix",
    "Name": "name",
    "Description": "description",
    "Homepage": "homepage",
    "Example Identifier": "example",
    "Regular Expression Pattern": "pattern",
}


def get_prefix_issues() -> Mapping[int, Tuple[str, Resource]]:
    """Get Bioregistry prefix issues from the GitHub API."""
    data = get_form_data("bioregistry", "bioregistry", ["New", "Prefix"], token=TOKEN)
    rv = {}
    for issue_id, resource_data in data.items():
        prefix = resource_data.pop("prefix")
        if bioregistry.get_resource(prefix) is not None:
            # TODO close issue
            logger.warning(
                "Issue is for duplicate prefix %s in https://github.com/bioregistry/bioregistry/issues/%s",
                prefix,
                issue_id,
            )
            continue
        resource = Resource(**resource_data)
        add_resource(prefix, resource)
        rv[issue_id] = prefix, resource
    return rv


def open_bioregistry_pr(
    *,
    title: str,
    head: str,
    body: Optional[str] = None,
):
    """Open a pull request for the Bioregistry."""
    rv = open_pull_request(
        owner="bioregistry",
        repo="bioregistry",
        base=MAIN_BRANCH,
        title=title,
        head=head,
        body=body,
        token=TOKEN,
    )
    print(rv)
    return rv


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
    headers = {
        "Accept": "application/vnd.github.v3+json",
    }
    if token:
        headers["Authorization"] = f"token {token}"

    data = {
        "title": title,
        "head": head,
        "base": base,
    }
    if body:
        data["body"] = body
    res = requests.post(
        f"https://api.github.com/repos/{owner}/{repo}/pulls",
        headers=headers,
        data=data,
    )
    return res.json()


def get_form_data(
    owner: str,
    repo: str,
    labels: Iterable[str],
    token: Optional[str] = None,
) -> Mapping[int, Dict[str, str]]:
    """Get parsed form data from issues matching the given labels.

    :param owner: The name of the owner/organization for the repository.
    :param repo: The name of the repository.
    :param labels: Labels to match
    :param token: The GitHub OAuth token. Not required, but if given, will let
        you make many more queries before getting rate limited.
    :return: A mapping from github issue issue data
    """
    headers = {
        "Accept": "application/vnd.github.v3+json",
    }
    if token:
        headers["Authorization"] = f"token {token}"

    labels = labels if isinstance(labels, str) else ",".join(labels)
    res = requests.get(
        f"https://api.github.com/repos/{owner}/{repo}/issues",
        headers=headers,
        params={
            "labels": labels,
            "state": "open",
        },
    )

    return {issue["number"]: parse_remap(issue["body"]) for issue in res.json()}


def parse_remap(body: str) -> Dict[str, Any]:
    """Parse the body string from a GitHub issue (via the API) and remap the header keys.

    :param body: The body string from a GitHub issue (via the API) that corresponds to a form
    :returns: A dictionary of keys (headers) to values, remapped to bioregistry internal keys
    """
    return remap(parse_body(body), MAPPING)


def remap(d: Dict[str, Any], m: Mapping[str, str]) -> Dict[str, Any]:
    """Map the keys in dictionary ``d`` based on dictionary ``m``."""
    return {m[k]: v for k, v in d.items()}


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
        if rest == "_No response_":
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
        except CalledProcessError:
            return None
        else:
            return ret.strip().decode("utf-8")


@click.command()
@click.option("--dry", is_flag=True)
@verbose_option
def main(dry: bool):
    """Run the automatic curator."""
    _status_porcelain = status_porcelain()
    if _status_porcelain:
        click.secho(f"The working directory is dirty:\n\n{_status_porcelain}", fg="red")
        sys.exit(0)

    github_id_to_prefix = get_prefix_issues()

    prefixes = sorted(prefix for prefix, _ in github_id_to_prefix.values())
    if len(prefixes) == 1:
        title = f"Add prefix {prefixes[0]}"
    elif len(prefixes) == 3:
        title = f"Add prefixes {prefixes[0]} and {prefixes[1]}"
    else:
        title = f'Add prefixes {", ".join(prefixes[:-1])}, and {prefixes[-1]}'

    body = ", ".join(f"Closes #{issue}" for issue in github_id_to_prefix)
    message = f"{title}\n\n{body}"
    branch_name = str(uuid4())[:8]
    if dry:
        click.secho(
            f"skipping making branch {branch_name}, committing, pushing, and PRing", fg="yellow"
        )
        sys.exit(0)

    click.secho("creating branch", fg="green")
    click.echo(branch(branch_name))
    click.secho("committing", fg="green")
    click.echo(commit(message, BIOREGISTRY_PATH.as_posix()))
    click.secho("pushing", fg="green")
    click.echo(push("origin", branch_name))
    click.secho(f"opening PR from {branch_name} to {MAIN_BRANCH}", fg="green")
    time.sleep(2)  # avoid race condition?
    open_bioregistry_pr(
        title=title,
        head=branch_name,
        body=body,
    )


if __name__ == "__main__":
    main()
