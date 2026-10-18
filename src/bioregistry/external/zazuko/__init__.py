"""Download Zazuko."""

import json
from collections.abc import Sequence
from pathlib import Path
from typing import ClassVar

import requests

from bioregistry.alignment_model import Artifact, ArtifactType, Record
from bioregistry.constants import URI_FORMAT_KEY
from pystow.utils import read_rdflib
from bioregistry.external.alignment_utils import Aligner, build_getter, cleanup_json

__all__ = [
    "ZazukoAligner",
    "get_zazuko",
    "parse_zazuko_raw",
]

DIRECTORY = Path(__file__).parent.resolve()
RAW_PATH = DIRECTORY / "raw.json"
PROCESSED_PATH = DIRECTORY / "processed.json"
URL = "https://prefix.zazuko.com/api/v1/prefixes"


def parse_zazuko_raw(path: Path) -> dict[str, Record]:
    """Parse Zazuko raw JSON data."""
    data = json.loads(path.read_text())
    rv = {}
    for prefix, uri_prefix in data.items():
        url = f"https://github.com/zazuko/rdf-vocabularies/raw/refs/heads/master/ontologies/{prefix}/package.json"
        res = requests.get(url, timeout=5)
        res.raise_for_status()
        res_json = res.json()

        # metadata available in triples at
        # full vocabulary available at

        metadata_url = f"https://github.com/zazuko/rdf-vocabularies/raw/refs/heads/master/ontologies/{prefix}/meta.nt"
        graph = read_rdflib(url)
        """
        <https://prefix.zazuko.com/bibo:> <http://dbpedia.org/ontology/filename> "@vocabulary/bibo/bibo.nq" .
        <https://prefix.zazuko.com/bibo:> <http://purl.org/dc/terms/description> "The Bibliographic Ontology describes\nbibliographic things on the semantic Web in RDF.  This ontology can be\nused as a citation ontology, as a document classification ontology, or\nsimply as a way to describe any kind of document in RDF. It has been\ninspired by many existing document description metadata formats, and\ncan be used as a common ground for converting other bibliographic data\nsources." .
        <https://prefix.zazuko.com/bibo:> <http://purl.org/dc/terms/title> "The Bibliographic Ontology" .
        <https://prefix.zazuko.com/bibo:> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.w3.org/ns/rdfa#PrefixMapping> .
        <https://prefix.zazuko.com/bibo:> <http://www.w3.org/2000/01/rdf-schema#isDefinedBy> <http://purl.org/ontology/bibo/> .
        <https://prefix.zazuko.com/bibo:> <http://www.w3.org/ns/rdfa#prefix> "bibo" .
        <https://prefix.zazuko.com/bibo:> <http://www.w3.org/ns/rdfa#uri> <http://purl.org/ontology/bibo/> .
        """

        rv[prefix] = Record(
            uri_format=f"{uri_prefix.strip()}$1",
            description=res_json.get("description"),
            homepage=res_json.get("homepage"),
            artifacts=[
                Artifact(
                    url=f"https://github.com/zazuko/rdf-vocabularies/blob/master/ontologies/{prefix}/{prefix}.nq",
                    type=ArtifactType.rdf,
                ),
            ],
        )
    return rv


get_zazuko = build_getter(
    processed_path=PROCESSED_PATH,
    raw_path=RAW_PATH,
    url=URL,
    func=parse_zazuko_raw,
    cleanup=cleanup_json,
    download_kwargs={"backend": "requests"},
)


class ZazukoAligner(Aligner):
    """Aligner for Zazuko."""

    key = "zazuko"
    getter = get_zazuko
    curation_header: ClassVar[Sequence[str]] = [URI_FORMAT_KEY]


if __name__ == "__main__":
    ZazukoAligner.cli()
