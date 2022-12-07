# -*- coding: utf-8 -*

"""Large data chunks for the web app."""

from bioregistry import version

__all__ = [
    "BIOSCHEMAS",
]

BIOSCHEMAS = {
    "@context": "http://schema.org/",
    "@type": "DataSet",
    "name": "Bioregistry",
    "description": "The Bioregistry is an open source, community curated registry,"
    " meta-registry, and compact identifier resolver",
    "url": "https://bioregistry.io",
    "version": version.get_version(),
    "license": "https://creativecommons.org/publicdomain/zero/1.0/",
    "keywords": [
        "registry",
        "life sciences",
        "compact identifier",
        "semantics",
        "biosemantics",
        "resolver",
    ],
    "creator": [
        {
            "givenName": "Charles Tapley",
            "familyName": "Hoyt",
            "email": "cthoyt@gmail.com",
            "url": "https://cthoyt.com",
            "name": "Charles Tapley Hoyt",
            "orcid": "https://orcid.org/0000-0003-4423-4370",
            "@type": "Person",
        }
    ],
    "provider": {
        "@type": "Organization",
        "name": "Harvard Medical School",
        "url": "https://hms.harvard.edu/",
    },
    "citation": "https://doi.org/10.1038/s41597-022-01807-3",
    "distribution": [
        {
            "contentUrl": "https://github.com/biopragmatics/bioregistry/blob/main/docs/_data/bioregistry.ttl",
            "encodingFormat": "text/turtle",
            "@type": "DataDownload",
        },
        {
            "contentUrl": "https://github.com/biopragmatics/bioregistry/blob/main/docs/_data/bioregistry.nt",
            "encodingFormat": "application/n-triples",
            "@type": "DataDownload",
        },
        {
            "contentUrl": "https://github.com/biopragmatics/bioregistry/blob/main/docs/_data/bioregistry.jsonld",
            "encodingFormat": "application/ld+json",
            "@type": "DataDownload",
        },
    ],
}
