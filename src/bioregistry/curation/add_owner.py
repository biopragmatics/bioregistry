"""Add owner."""

from urllib.parse import urlparse

import click
import ror_downloader
from tabulate import tabulate

import bioregistry


def main() -> None:
    """Add organization."""
    domain_to_organization = {
        domain: organization
        for organization in ror_downloader.get_organizations()[1]
        for domain in organization.domains
    }
    rows = []
    for resource in bioregistry.resources():
        if resource.get_owners():
            continue
        homepage = resource.get_homepage()
        if not homepage or "www.w3.org" in homepage:
            continue

        domain = urlparse(homepage).netloc
        if not domain:
            continue

        if org := domain_to_organization.get(domain):
            rows.append((resource.prefix, domain, org.id, org.get_preferred_label()))
        elif org := domain_to_organization.get(domain.removeprefix("www.")):
            rows.append((resource.prefix, domain, org.id, org.get_preferred_label()))

    click.echo(tabulate(rows, tablefmt="github"))


if __name__ == "__main__":
    main()
