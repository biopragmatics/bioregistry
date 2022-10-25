# -*- coding: utf-8 -*-

"""A script for creating pull requests for each new prefix issue on the Bioregistry's GitHub page.

Run with: ``python -m bioregistry.gh.new_prefix``
"""

import logging
import sys
import time
from typing import Dict, Iterable, Mapping, Optional, Sequence
from uuid import uuid4

import click
from more_click import force_option, verbose_option

import bioregistry
from bioregistry.constants import BIOREGISTRY_PATH, URI_FORMAT_KEY
from bioregistry.gh import github_client
from bioregistry.schema import Author, Resource
from bioregistry.schema_utils import add_resource
from bioregistry.utils import removeprefix

logger = logging.getLogger(__name__)

#: A mapping from the headers in the GitHub new prefix form to Bioregistry internal keys
MAPPING = {
    "Prefix": "prefix",
    "Name": "name",
    "Homepage": "homepage",
    "Description": "description",
    "Example Identifier": "example",  # old
    "Example Local Unique Identifier": "example",
    "Regular Expression Pattern": "pattern",  # old
    "Regular Expression Pattern for Local Unique Identifier": "pattern",
    "Redundant Prefix in Regular Expression Pattern": "banana",
    "Provider Format URL": URI_FORMAT_KEY,  # old
    "URI Format String": URI_FORMAT_KEY,
    "Additional Comments": "comment",
    "Contributor ORCiD": "contributor_orcid",
    "Contributor Name": "contributor_name",
    "Contributor GitHub": "contributor_github",
    "Contributor Email": "contributor_email",
    "Contact ORCiD": "contact_orcid",
    "Contact Name": "contact_name",
    "Contact Email": "contact_email",
    "Contact GitHub": "contact_github",
    "Wikidata Property": "wikidata_prefix",
    "License": "license",
    "Repository": "repository",
}

ORCID_HTTP_PREFIX = "http://orcid.org/"
ORCID_HTTPS_PREFIX = "https://orcid.org/"


def get_new_prefix_issues(token: Optional[str] = None) -> Mapping[int, Resource]:
    """Get Bioregistry prefix issues from the GitHub API.

    This is done by filtering on issues containing the "New" and "Prefix" labels.

    .. todo::

        Issues corresponding to a prefix that is already in the Bioregistry should be sent a message then
        automatically closed

    :param token: The GitHub OAuth token. Not required, but if given, will let
        you make many more queries before getting rate limited.
    :returns: A mapping of issue identifiers to pairs of the prefix itself and a :class:`Resource` instance
        that has been parsed out of the issue form
    """
    data = github_client.get_bioregistry_form_data(
        ["New", "Prefix"], remapping=MAPPING, token=token
    )
    rv: Dict[int, Resource] = {}
    for issue_id, resource_data in data.items():
        prefix = resource_data.pop("prefix").lower()
        contributor = Author(
            name=resource_data.pop("contributor_name"),
            orcid=_pop_orcid(resource_data),
            email=resource_data.pop("contributor_email", None),
            github=removeprefix(resource_data.pop("contributor_github"), "@"),
        )

        contact_name = resource_data.pop("contact_name", None)
        contact_orcid = resource_data.pop("contact_orcid", None)
        contact_email = resource_data.pop("contact_email", None)
        contact_github = removeprefix(resource_data.pop("contact_github", None), "@")
        if contact_orcid:
            contact = Author(
                name=contact_name,
                orcid=_trim_orcid(contact_orcid),
                email=contact_email,
                github=contact_github,
            )
        else:
            contact = None

        wikidata_property = resource_data.pop("wikidata_prefix", None)
        wikidata: Optional[Mapping]
        mappings: Optional[Mapping]
        if wikidata_property:
            wikidata = {"prefix": wikidata_property}
            mappings = {"wikidata": wikidata_property}
        else:
            wikidata = mappings = None

        # Remove redundant prefix from identifier if given as a CURIE
        if "example" in resource_data and resource_data["example"].startswith(f"{prefix}:"):
            resource_data["example"] = resource_data["example"][len(prefix) + 1 :]

        # Capitalize the description
        resource_data["description"] = resource_data["description"]

        # Ensure the pattern is delimited properly
        pattern = resource_data.get("pattern")
        if pattern:
            resource_data["pattern"] = "^" + pattern.lstrip("^").rstrip("$") + "$"

        if bioregistry.get_resource(prefix) is not None:
            # TODO close issue
            logger.warning(
                "Issue is for duplicate prefix %s in https://github.com/biopragmatics/bioregistry/issues/%s",
                prefix,
                issue_id,
            )
            continue
        rv[issue_id] = Resource(
            prefix=prefix,
            contributor=contributor,
            contact=contact,
            github_request_issue=issue_id,
            wikidata=wikidata,
            mappings=mappings,
            **resource_data,
        )
    return rv


def _pop_orcid(data: Dict[str, str]) -> str:
    orcid = data.pop("contributor_orcid")
    return _trim_orcid(orcid)


def _trim_orcid(orcid: str) -> str:
    if orcid.startswith(ORCID_HTTP_PREFIX):
        return orcid[len(ORCID_HTTP_PREFIX) :]
    if orcid.startswith(ORCID_HTTPS_PREFIX):
        return orcid[len(ORCID_HTTPS_PREFIX) :]
    return orcid


def _join(x: Iterable[int], sep=", ") -> str:
    return sep.join(map(str, sorted(x)))


def make_title(prefixes: Sequence[str]) -> str:
    """Make a title for the PR."""
    if len(prefixes) == 0:
        raise ValueError
    if len(prefixes) == 1:
        return f"Add prefix: {prefixes[0]}"
    elif len(prefixes) == 2:
        return f"Add prefixes: {prefixes[0]} and {prefixes[1]}"
    else:
        return f'Add prefixes: {", ".join(prefixes[:-1])}, and {prefixes[-1]}'


@click.command()
@click.option("--dry", is_flag=True, help="Dry run - do not create any PRs")
@click.option("--github", is_flag=True, help="Use this flag in a GHA setting to set run variables")
@force_option
@verbose_option
def main(dry: bool, github: bool, force: bool):
    """Run the automatic curator."""
    status_porcelain_result = github_client.status_porcelain()
    if status_porcelain_result and not force and not dry:
        click.secho(f"The working directory is dirty:\n\n{status_porcelain_result}", fg="red")
        sys.exit(1)

    if not github_client.has_token():
        click.secho("No GitHub access token is available through GITHUB_TOKEN", fg="red")
        sys.exit(1)

    issue_to_resource = get_new_prefix_issues()
    if issue_to_resource:
        click.echo(f"Found {len(issue_to_resource)} new prefix issues:")
        for issue_number in sorted(issue_to_resource, reverse=True):
            link = click.style(
                f"https://github.com/biopragmatics/bioregistry/issues/{issue_number}", fg="cyan"
            )
            click.echo(f" - {link}")
    else:
        click.echo("Found no new prefix issues")

    pulled_issues = github_client.get_issues_with_pr(issue_to_resource)
    if pulled_issues:
        click.echo(f"Found PRs covering {len(pulled_issues)} new prefix issues:")
        for pr_number in sorted(pulled_issues, reverse=True):
            link = click.style(
                f"https://github.com/biopragmatics/bioregistry/pulls/{pr_number}", fg="cyan"
            )
            click.echo(f" - {link}")
    else:
        click.echo("Found no PRs covering new prefix issues")

    # filter out issues that already have an associated pull request
    issue_to_resource = {
        issue_id: value
        for issue_id, value in issue_to_resource.items()
        if issue_id not in pulled_issues
    }

    if issue_to_resource:
        click.echo(f"Adding {len(issue_to_resource)} issues after filter")
    else:
        click.secho("No issues without PRs to worry about. Exiting.")
        sys.exit(0)

    for issue_number, resource in issue_to_resource.items():
        click.echo(f"🚀 Adding resource {resource.prefix} (#{issue_number})")
        add_resource(resource)

    title = make_title(sorted(resource.prefix for resource in issue_to_resource.values()))
    body = ", ".join(f"Closes #{issue}" for issue in issue_to_resource)
    message = f"{title}\n\n{body}"
    branch_name = str(uuid4())[:8]

    if github:
        click.echo(
            f"""
          ::set-output name=BR_BODY::{body}
          ::set-output name=BR_TITLE::{title}
        """
        )
        return sys.exit(0)
    elif dry:
        click.secho(
            f"skipping making branch {branch_name}, committing, pushing, and PRing", fg="yellow"
        )
        return sys.exit(0)

    click.secho("creating and switching to branch", fg="green")
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

    click.secho(f"switching back to {github_client.MAIN_BRANCH} branch", fg="green")
    click.echo(github_client.home())


if __name__ == "__main__":
    main()
