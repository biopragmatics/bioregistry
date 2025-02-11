"""Find group emails."""

from bioregistry.constants import DISALLOWED_EMAIL_PARTS
import bioregistry
from tabulate import tabulate


def main() -> None:
    """Find group mails."""
    rows = []
    for resource in bioregistry.resources():
        contact = resource.get_contact()
        if not contact or not contact.email:
            continue
        if any(
            p in contact.email
            for p in DISALLOWED_EMAIL_PARTS
        ):
            rows.append((resource.prefix, resource.get_name(), contact.name, contact.email))
    print(tabulate(rows))


if __name__ == '__main__':
    main()
