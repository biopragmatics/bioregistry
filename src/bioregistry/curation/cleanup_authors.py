"""Add ragged ORCID, email, and GitHub."""

from collections import defaultdict

from bioregistry import Author, Manager
from bioregistry.curation.utils import manager_mutator
from bioregistry.schema import Attributable


@manager_mutator()
def cleanup_authors(manager: Manager) -> None:
    """Standardize author names, emails, and GitHub links."""
    githubs, emails = {}, {}
    names: defaultdict[str, set[str]] = defaultdict(set)
    for resource in manager.registry.values():
        authors = [
            resource.contributor,
            resource.contact,
            resource.reviewer,
            *(resource.contributor_extras or []),
            *(resource.reviewer_extras or []),
            *(resource.contact_extras or []),
        ]
        for author in authors:
            if author is None:
                continue
            orcid = author.orcid
            if orcid is None:
                continue
            if author.name:
                names[orcid].add(author.name)
            if author.github:
                githubs[orcid] = author.github
            if author.email and orcid not in emails:
                # TODO lowercase?
                emails[orcid] = author.email

    # Chose the longest name, assuming that contains the least abbreviations and most initials
    orcid_to_name: dict[str, str] = {
        orcid: max(all_names, key=len) for orcid, all_names in names.items()
    }

    def _new_attributable(orcid_: str) -> Attributable:
        return Attributable(
            orcid=orcid_,
            name=orcid_to_name[orcid_],
            email=emails.get(orcid_),
            github=githubs.get(orcid_),
        )

    def _new_author(orcid_: str) -> Author:
        return Author(
            orcid=orcid_,
            name=orcid_to_name[orcid_],
            email=emails.get(orcid_),
            github=githubs.get(orcid_),
        )

    for resource in manager.registry.values():
        if resource.contributor and resource.contributor.orcid:
            resource.contributor = _new_author(resource.contributor.orcid)
        if resource.contributor_extras:
            resource.contributor_extras = [
                _new_author(contributor.orcid) if contributor.orcid else contributor
                for contributor in resource.contributor_extras
            ]

        if resource.reviewer and resource.reviewer.orcid:
            resource.reviewer = _new_author(resource.reviewer.orcid)
        if resource.reviewer_extras:
            resource.reviewer_extras = [
                _new_author(reviewer.orcid) if reviewer.orcid else reviewer
                for reviewer in resource.reviewer_extras
            ]

        if resource.contact and resource.contact.orcid:
            resource.contact = _new_attributable(resource.contact.orcid)
        if resource.contact_extras:
            resource.contact_extras = [
                _new_attributable(contact.orcid) if contact.orcid else contact
                for contact in resource.contact_extras
            ]


if __name__ == "__main__":
    cleanup_authors()
