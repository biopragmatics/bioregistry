"""Large data chunks for the web app."""

from .. import version
from ..constants import INTERNAL_LABEL, INTERNAL_REPOSITORY_BLOB

__all__ = [
    "BIOSCHEMAS",
]

BIOSCHEMAS = {
    "@context": "http://schema.org/",
    "@type": "DataSet",
    "name": INTERNAL_LABEL,
    # Maybe externalize the description, too
    "description": f"The {INTERNAL_LABEL} is an open source, community curated registry,"
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
        "name": "RWTH Aachen University",
        "url": "https://rwth-aachen.de",
    },
    "citation": "https://doi.org/10.1038/s41597-022-01807-3",
    "distribution": [
        {
            "contentUrl": f"{INTERNAL_REPOSITORY_BLOB}/docs/_data/bioregistry.ttl",
            "encodingFormat": "text/turtle",
            "@type": "DataDownload",
        },
        {
            "contentUrl": f"{INTERNAL_REPOSITORY_BLOB}/docs/_data/bioregistry.nt",
            "encodingFormat": "application/n-triples",
            "@type": "DataDownload",
        },
        {
            "contentUrl": f"{INTERNAL_REPOSITORY_BLOB}/main/docs/_data/bioregistry.jsonld",
            "encodingFormat": "application/ld+json",
            "@type": "DataDownload",
        },
    ],
}

KEY_A = "df1808a3"
KEY_B = "0d15"
KEY_C = "4e75"
KEY_D = "9b71"
KEY_E = "b9e7da1d6ac3"
