"""Find group emails."""

import click
from tabulate import tabulate

import bioregistry
from bioregistry.constants import DISALLOWED_EMAIL_PARTS

#: emails that are actually from people, but might get flagged as not
ALLOWLIST = {
    "allyson.lister@oerc.ox.ac.uk",
    "alistair.miles@linacre.ox.ac.uk",
}


@click.command()
def main() -> None:
    """Find group mails."""
    rows = []
    for resource in bioregistry.resources():
        contact = resource.get_contact()
        if not contact or not contact.email:
            continue
        if contact.email in ALLOWLIST:
            continue
        if any(p in contact.email for p in DISALLOWED_EMAIL_PARTS | {"help", "list"}) or any(
            p in contact.name.lower() for p in {"helpdesk", "support"}
        ):
            publications = resource.get_publications()
            if publications:
                url = publications[0].get_url()
            else:
                url = ""

            rows.append((resource.prefix, resource.get_name(), contact.name, contact.email, url))
    click.echo(tabulate(rows))


if __name__ == "__main__":
    main()
