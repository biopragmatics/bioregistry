"""Large data chunks for the web app."""

from __future__ import annotations

from pathlib import Path

from .. import version
from ..constants import INTERNAL_LABEL, INTERNAL_REPOSITORY_BLOB

__all__ = [
    "BIOSCHEMAS",
    "FORMATS",
    "KEY_TO_MIMETYPE",
    "MIMETYPE_SYNONYM_TO_CANONICAL",
    "MIMETYPE_TO_RDFLIB_FORMAT",
    "TEMPLATES_DIRECTORY",
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

#: A mapping of mimetypes to RDFLib formats
MIMETYPE_TO_RDFLIB_FORMAT = {
    "text/turtle": "turtle",
    "application/ld+json": "json-ld",
    "application/rdf+xml": "xml",
    "text/n3": "n3",
}

#: keys exposed through the API to map back to mimetypes
KEY_TO_MIMETYPE = {
    "json": "application/json",
    "yml": "application/yaml",
    "yaml": "application/yaml",
    "turtle": "text/turtle",
    "jsonld": "application/ld+json",
    "json-ld": "application/ld+json",
    "rdf": "application/rdf+xml",
    "n3": "text/n3",
}

MIMETYPE_SYNONYM_TO_CANONICAL = {
    "text/json": "application/json",
    "text/yaml": "application/yaml",
}
TEMPLATES_DIRECTORY = Path(__file__).parent.resolve().joinpath("templates")
FORMATS = [
    ("JSON", "json"),
    ("YAML", "yaml"),
]
