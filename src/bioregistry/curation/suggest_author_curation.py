"""Suggest curation of authors missing orcid/github."""

from collections import defaultdict

import click
from tabulate import tabulate

import bioregistry


def _main():
    rows = defaultdict(set)
    for resource in bioregistry.resources():
        contact = resource.get_contact()
        if not contact:
            continue
        if contact.orcid and contact.email and contact.github:
            continue
        rows[
            contact.name or "", contact.orcid or "", contact.email or "", contact.github or ""
        ].add(resource.prefix)

    click.echo(
        tabulate(
            [
                (name, orcid, email, github, ", ".join(sorted(prefixes)))
                for (name, orcid, email, github), prefixes in sorted(
                    rows.items(), key=lambda t: (t[0][0].casefold(), t[0][0])
                )
            ],
            tablefmt="github",
            headers=["name", "orcid", "email", "github", "prefixes"],
        )
    )


if __name__ == "__main__":
    _main()
