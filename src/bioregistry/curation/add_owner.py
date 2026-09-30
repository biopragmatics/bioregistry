"""Add owner."""

from urllib.parse import urlparse

import click
import ror_downloader
from tabulate import tabulate

import bioregistry
from bioregistry import Organization

SKIP_PREFIXES = {"worldavatar.os"}


def main() -> None:
    """Add organization."""
    domain_to_organization = {
        domain: organization
        for organization in ror_downloader.get_organizations()[1]
        for domain in organization.domains
    }
    rows = []
    for resource in bioregistry.manager.registry.values():
        if resource.get_owners() or resource.prefix in SKIP_PREFIXES:
            continue
        homepage = resource.get_homepage()
        if not homepage or "www.w3.org" in homepage:
            continue

        domain = urlparse(homepage).netloc
        if not domain:
            continue

        org = domain_to_organization.get(domain)
        if not org:
            org = domain_to_organization.get(domain.removeprefix("www."))
        if not org:
            continue
        rows.append((resource.prefix, domain, org.id, org.get_preferred_label()))
        resource.owners = [
            Organization(
                name=org.get_preferred_label(), ror=org.id.removeprefix("https://ror.org/")
            )
        ]
    bioregistry.manager.write_registry()

    click.echo(tabulate(rows, tablefmt="github"))


if __name__ == "__main__":
    main()
