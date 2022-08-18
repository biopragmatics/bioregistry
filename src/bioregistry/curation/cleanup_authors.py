"""Add ragged ORCID, email, and GitHub."""

from collections import defaultdict

from bioregistry import manager
from bioregistry.schema import Attributable


def _main():
    githubs, emails = {}, {}
    names = defaultdict(set)
    for resource in manager.registry.values():
        authors = [
            resource.contributor,
            resource.contributor,
            resource.contact,
            resource.reviewer,
            *(resource.contributor_extras or []),
        ]
        for author in authors:
            if author is None:
                continue
            orcid = author.orcid
            names[orcid].add(author.name)
            if author.github:
                githubs[orcid] = author.github
            if author.email:
                emails[orcid] = author.email

    nn = {orcid: max(all_names, key=len) for orcid, all_names in names.items()}

    def _new(orcid: str) -> Attributable:
        return Attributable(
            orcid=orcid,
            name=nn[orcid],
            email=emails.get(orcid),
            github=githubs.get(orcid),
        )

    for resource in manager.registry.values():
        if resource.contributor:
            resource.contributor = _new(resource.contributor.orcid)
        if resource.reviewer:
            resource.reviewer = _new(resource.reviewer.orcid)
        if resource.contact:
            resource.contact = _new(resource.contact.orcid)
        if resource.contributor_extras:
            resource.contributor_extras = [
                _new(contributor.orcid) if contributor.orcid else contributor
                for contributor in resource.contributor_extras
            ]

    manager.write_registry()


if __name__ == "__main__":
    _main()
