# -*- coding: utf-8 -*-

"""A script for creating pull requests for each new prefix issue on the Bioregistry's GitHub page.

Run with: ``python -m bioregistry.gh.new_prefix``
"""

import logging
import sys
import time
from typing import Mapping, Sequence, Tuple
from uuid import uuid4

import click
from more_click import verbose_option

import bioregistry
from bioregistry.constants import BIOREGISTRY_PATH
from bioregistry.schema import Resource
from bioregistry.utils import add_resource
from . import github_client

logger = logging.getLogger(__name__)

#: A mapping from the headers in the GitHub new prefix form to Bioregistry internal keys
MAPPING = {
    "Prefix": "prefix",
    "Name": "name",
    "Description": "description",
    "Homepage": "homepage",
    "Example Identifier": "example",
    "Regular Expression Pattern": "pattern",
}


def get_new_prefix_issues() -> Mapping[int, Tuple[str, Resource]]:
    """Get Bioregistry prefix issues from the GitHub API.

    This is done by filtering on issues containing the "New" and "Prefix" labels.

    .. todo::

        Issues corresponding to a prefix that is already in the Bioregistry should be sent a message then
        automatically closed

    :returns: A mapping of issue identifiers to pairs of the prefix itself and a :class:`Resource` instance
        that has been parsed out of the issue form
    """
    data = github_client.get_bioregistry_form_data(["New", "Prefix"], remapping=MAPPING)
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
        rv[issue_id] = prefix, Resource(**resource_data)
    return rv


def _join(x, sep=',') -> str:
    return sep.join(map(str, x))


def make_title(prefixes: Sequence[str]) -> str:
    if len(prefixes) == 0:
        raise ValueError
    if len(prefixes) == 1:
        return f"Add prefix: {prefixes[0]}"
    elif len(prefixes) == 2:
        return f"Add prefixes: {prefixes[0]} and {prefixes[1]}"
    else:
        return f'Add prefixes: {", ".join(prefixes[:-1])}, and {prefixes[-1]}'


@click.command()
@click.option("--dry", is_flag=True)
@verbose_option
def main(dry: bool):
    """Run the automatic curator."""
    status_porcelain_result = github_client.status_porcelain()
    if status_porcelain_result:
        click.secho(f"The working directory is dirty:\n\n{status_porcelain_result}", fg="red")
        sys.exit(0)

    issue_to_resource = get_new_prefix_issues()
    click.echo(f'Got {len(issue_to_resource)} issues: {_join(issue_to_resource)}')

    pulled_issues = github_client.get_issues_with_pr(issue_to_resource)
    click.echo(f'Got {len(pulled_issues)} PRs: {_join(pulled_issues)}')

    # filter out issues that already have an associated pull request
    issue_to_resource = {
        issue_id: value
        for issue_id, value in issue_to_resource.items()
        if issue_id not in pulled_issues
    }
    click.echo(
        f'Remaining {len(issue_to_resource)} issues after filter: {_join(issue_to_resource)}'
    )

    if not issue_to_resource:
        click.secho("No issues to worry about")
        sys.exit(0)

    # Add resources
    for prefix, resource in issue_to_resource.values():
        click.echo(f'Adding resource {prefix}')
        add_resource(prefix, resource)

    title = make_title(sorted(prefix for prefix, _ in issue_to_resource.values()))
    body = ", ".join(f"Closes #{issue}" for issue in issue_to_resource)
    message = f"{title}\n\n{body}"
    branch_name = str(uuid4())[:8]
    if dry:
        click.secho(
            f"skipping making branch {branch_name}, committing, pushing, and PRing", fg="yellow"
        )
        sys.exit(0)

    click.secho("creating branch", fg="green")
    click.echo(github_client.branch(branch_name))
    click.secho("committing", fg="green")
    click.echo(github_client.commit(message, BIOREGISTRY_PATH.as_posix()))
    click.secho("pushing", fg="green")
    click.echo(github_client.push("origin", branch_name))
    click.secho(f"opening PR from {branch_name} to {github_client.MAIN_BRANCH}", fg="green")
    time.sleep(2)  # avoid race condition?
    rv = github_client.open_bioregistry_pull_request(
        title=title,
        head=branch_name,
        body=body,
    )
    if "url" in rv:
        click.secho(f'PR at {rv["url"]}')
    else:  # probably an error
        click.secho(rv, fg="red")


if __name__ == "__main__":
    main()
