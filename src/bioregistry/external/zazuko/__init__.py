"""Download Zazuko."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import TYPE_CHECKING

import pystow
import requests
from tqdm import tqdm

from bioregistry.alignment_model import Artifact, ArtifactType, Record
from bioregistry.external.alignment_utils import Aligner, build_getter, cleanup_json

if TYPE_CHECKING:
    from rdflib import Graph, URIRef

__all__ = [
    "ZazukoAligner",
    "get_zazuko",
    "parse_zazuko_raw",
]

DIRECTORY = Path(__file__).parent.resolve()
RAW_PATH = DIRECTORY / "raw.json"
PROCESSED_PATH = DIRECTORY / "processed.json"
URL = "https://prefix.zazuko.com/api/v1/prefixes"


def parse_zazuko_raw(path: Path, *, refresh: bool = False) -> dict[str, Record]:
    """Parse Zazuko raw JSON data."""
    from rdflib import DCTERMS, RDFS, URIRef

    data = json.loads(path.read_text())
    rv = {}
    Counter()
    for prefix, uri_prefix in tqdm(data.items(), leave=False, desc="downloading Zazuko"):
        url = f"https://github.com/zazuko/rdf-vocabularies/raw/refs/heads/master/ontologies/{prefix}/package.json"
        res = requests.get(url, timeout=5)
        res.raise_for_status()
        res_json = res.json()

        metadata_url = f"https://github.com/zazuko/rdf-vocabularies/raw/refs/heads/master/ontologies/{prefix}/meta.nt"
        graph = pystow.ensure_rdf(
            "bioregistry", "zazuko", url=metadata_url, name=f"{prefix}-meta.nt", force=refresh
        )
        node = URIRef(f"https://prefix.zazuko.com/{prefix}:")

        rv[prefix] = Record(
            uri_format=f"{uri_prefix.strip()}$1",
            name=_get_one(graph, node, DCTERMS.title),
            description=_get_one(graph, node, DCTERMS.description) or res_json.get("description"),
            homepage=_get_one(graph, node, RDFS.isDefinedBy) or res_json.get("homepage"),
            artifacts=[
                Artifact(
                    url=f"https://github.com/zazuko/rdf-vocabularies/raw/refs/heads/master/ontologies/{prefix}/{prefix}.nq",
                    type=ArtifactType.rdf,
                ),
            ],
        )
    return rv


def _get_one(graph: Graph, node: URIRef, predicate: URIRef) -> str | None:
    import rdflib

    objects = list(graph.objects(node, predicate))
    if not objects:
        return None
    first = objects[0]
    if isinstance(first, rdflib.URIRef):
        return str(first)
    if isinstance(first, rdflib.Literal):
        return str(first)
    raise TypeError


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


if __name__ == "__main__":
    ZazukoAligner.cli()
