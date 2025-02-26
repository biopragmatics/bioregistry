"""Suggest curation of authors missing orcid/github."""

from collections import defaultdict

import click
from tabulate import tabulate

import bioregistry

# This keeps a list of group emails that are explicitly inappropriate
# for the bioregistry since we want single responsibility
EMAIL_BLACKLIST = {
    "agrovoc@fao.org",
    "swisslipids@isb-sib.ch",
    "Intellectual.PropertyServices@ama-assn.org",
    "ordo.orphanet@inserm.fr",
    "help@emdatabank.org",
    "biomodels-net-support@lists.sf.net",
    "support@bioontology.org",
    "chebi-help@ebi.ac.uk",
    "helpdesk@cropontology-curationtool.org",
    "ncictcaehelp@mail.nih.gov",
    "eugenes@iubio.bio.indiana.edu",
    "helpdesk@eionet.europa.eu",
    "faldo@googlegroups.com",
    "cs@firstdatabank.com",
    "itiswebmaster@itis.gov",
    "depod@embl.de",
    "datasubs@ebi.ac.uk",
    "curator@inoh.org",
    "support@bel.bio",
    "loinc@regenstrief.org",
    "info@who.int",
    "admin@envipath.org",
    "interhelp@ebi.ac.uk",
    "datex@efsa.europa.eu",
    "secretariat@eol.org",
    "whocc@fhi.no",
    "info@casrai.org",
    "ppdb@gifu-u.ac.jp",
}


def _main():
    rows = defaultdict(set)
    for resource in bioregistry.resources():
        if resource.is_deprecated():
            continue
        contact = resource.get_contact()
        if not contact:
            continue
        if contact.email in EMAIL_BLACKLIST:
            contact.email = None
        contact.name = contact.name.removeprefix("Dr. ").strip()
        contact.name = contact.name.removeprefix("Dr ").strip()
        contact.name = contact.name.removesuffix("MD").strip()
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
