"""Test prefix data for the new prefix pipeline."""

NCBIORTHOLOG_TEST = {
    "prefix": "ncbiortholog.test",
    "name": "National Center for Biotechnology Information",
    "homepage": "https://www.ncbi.nlm.nih.gov/gene/",
    "repository": "n/a",
    "description": (
        "Database of one-to-one ortholog information provided by the NCBI "
        "as a subset of their Gene resource. Used for users to access ortholog "
        "information for over 1000 species of vertebrates and arthropods."
    ),
    "license": "US gov't public domain",
    "example": "2",
    "pattern": "^\\d+$",
    "uri_format": "https://www.ncbi.nlm.nih.gov/gene/$1/ortholog/",
    "contributor_name": "Terence Murphy",
    "contributor_github": "murphyte",
    "contributor_orcid": "0000-0001-9311-9745",
    "contributor_email": "murphyte@ncbi.nlm.nih.gov",
    "contact_name": "Terence Murphy",
    "contact_orcid": "0000-0001-9311-9745",
    "contact_github": "murphyte",
    "contact_email": "murphyte@ncbi.nlm.nih.gov",
    "comment": (
        "We do not currently have the source code for our ortholog resource available publicly, "
        "although we are looking at how to split it off and make it available in the next year. "
        "We are now in the process of adding this tag to the INSDC list for use in annotations, "
        "so I'd like to mirror that tag in bioregistry."
    ),
}

VIBSO_TEST = {
    "prefix": "vibso.test",
    "name": "Vibrational Spectroscopy Ontology",
    "homepage": "https://nfdi4chem.github.io/VibrationalSpectroscopyOntology/",
    "repository": "https://github.com/NFDI4Chem/VibrationalSpectroscopyOntology",
    "description": (
        "The Vibration Spectroscopy Ontology defines technical terms with which research " 
        "data produced in vibrational spectroscopy experiments can be semantically " 
        "enriched, made machine readable and FAIR."
    ),
    "license": "https://creativecommons.org/licenses/by/4.0/",
    "example": "0000008",
    "pattern": "n/a",
    "uri_format": "http://purl.obolibrary.org/obo/VIBSO_$1",
    "contributor_name": "Philip Strömert",
    "contributor_github": "StroemPhi",
    "contributor_orcid": "0000-0002-1595-3213",
    "contributor_email": "philip.stroemert@tib.eu",
    "contact_name": "Philip Strömert",
    "contact_orcid": "0000-0002-1595-3213",
    "contact_github": "StroemPhi",
    "contact_email": "philip.stroemert@tib.eu",
    "comment": "n/a"
}