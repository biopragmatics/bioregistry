"""Suggest curation of authors missing ORCiD/GitHub."""

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
    "admin@admin.com",
    "contact-terminologietal@inist.fr",
    "register@clinicaltrials.gov",
    "esip-semanticweb@lists.esipfed.org",
    "mssohelp@meddra.org",
    "ncithesaurus@mail.nih.gov",
    "custserv@nlm.nih.gov",
    "OP-EU-VOCABULARIES@publications.europa.eu",
    "public-schemaorg@w3.org",
}

BAD_NAMES = {
    "WHO Collaborating Centre for Drug Statistics Methodology",
    "admin",
    "American Medical Association",
    "Biodiversity Thesaurus contact",
    "ClinicalTrials.gov Helpdesk",
    "UK Food Standard Agency",
    "Publications Office of the European Union",
    "World Health Organization",
    "the W3C Schema.org Community Group",
    "The World Health Organization",
    "NCI Thesaurus Mailbox",
    "RxNorm Customer Service",
    "UNESCO",
    "MedDRA MSSO",
    "IIS Helpdesk",
    "ICD Helpdesk",
    "ESIP Semantic Team",
    "Eionet Helpdesk",
    "NLM Customer Service",
    "NIH Reporter Helpdesk",
}

COULD_NOT_FIND_GITHUB = {
    "0000-0002-8527-5614",
}


def _main() -> None:
    curatable_people_rows = defaultdict(set)
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
        if contact.orcid and contact.orcid in COULD_NOT_FIND_GITHUB:
            continue
        if contact.name in BAD_NAMES:
            continue  # TODO add curation table for this too

        curatable_people_rows[
            contact.name or "", contact.orcid or "", contact.email or "", contact.github or ""
        ].add(resource.prefix)

    click.echo(
        tabulate(
            [
                (name, orcid, email, github, ", ".join(sorted(prefixes)))
                for (name, orcid, email, github), prefixes in sorted(
                    curatable_people_rows.items(), key=lambda t: (t[0][0].casefold(), t[0][0])
                )
            ],
            tablefmt="github",
            headers=["name", "orcid", "email", "github", "prefixes"],
        )
    )


if __name__ == "__main__":
    _main()
