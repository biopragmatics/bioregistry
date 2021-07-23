import logging
from typing import Iterable, Optional

import click
import more_itertools
import pystow
import requests
from more_click import verbose_option

import bioregistry
from bioregistry.schema import Resource
from bioregistry.utils import add_resource

logger = logging.getLogger(__name__)
TOKEN = pystow.get_config('github', 'access_token')


def has_topic(owner: str, repo: str, labels: Iterable[str], token: Optional[str] = None):
    """Check if the given GitHub repository has the given topic.

    :param owner: The name of the owner/organization for the repository.
    :param repo: The name of the repository.
    :param labels: Labels to match
    :param token: The GitHub OAuth token. Not required, but if given, will let
        you make many more queries before getting rate limited.
    :return: If the repository has the given topic.
    """
    headers = {
        'Accept': "application/vnd.github.v3+json",
    }
    if token:
        headers['Authorization'] = f"token {token}",

    labels = labels if isinstance(labels, str) else ','.join(labels)
    res = requests.get(
        f'https://api.github.com/repos/{owner}/{repo}/issues?labels={labels}&state=open',
        headers=headers,
    )

    prefix_to_issue_id = {}
    for issue in res.json():
        issue_id = issue['number']
        data = parse_remap(issue['body'])
        prefix = data.pop('prefix')
        if bioregistry.get_resource(prefix) is not None:
            # TODO close issue
            logger.info(
                'Issue is for duplicate prefix %s in https://github.com/bioregistry/bioregistry/issues/%s',
                prefix, issue_id,
            )
            continue
        resource = Resource(**data)
        add_resource(prefix, resource)
        logger.info('Added resource %s', prefix)
        prefix_to_issue_id[prefix] = issue_id
    return prefix_to_issue_id


MAPPING = {
    'Prefix': 'prefix',
    'Name': 'name',
    'Description': 'description',
    'Homepage': 'homepage',
    'Example Identifier': 'example',
    'Regular Expression Pattern': 'pattern',
}


def parse_remap(body):
    return remap(parse_body(body), MAPPING)


def remap(d, m):
    return {m[k]: v for k, v in d.items()}


def parse_body(body):
    rv = {}
    lines = [line.strip() for line in body.splitlines() if line.strip()]
    for group in more_itertools.split_before(lines, lambda line: line.startswith('### ')):
        header, *rest = group
        header = header.lstrip('#').lstrip()
        rest = ' '.join(x.strip() for x in rest)
        if rest == '_No response_':
            continue
        rv[header] = rest
    return rv


@click.command()
@verbose_option
def main():
    has_topic('bioregistry', 'bioregistry', ['New', 'Prefix'])


if __name__ == '__main__':
    main()
