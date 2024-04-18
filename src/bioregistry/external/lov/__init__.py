# -*- coding: utf-8 -*-

"""Download the LOV registry."""

import json
import tempfile
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Union

from pystow.utils import download, read_rdf

from bioregistry.external.alignment_utils import Aligner

__all__ = [
    "get_lov",
    "LOVAligner",
]

DIRECTORY = Path(__file__).parent.resolve()
PROCESSED_PATH = DIRECTORY / "processed.json"
URL = "https://lov.linkeddata.es/lov.n3.gz"


RECORD_SPARQL = """\
    SELECT ?vocab ?name ?prefix ?uri_prefix ?description ?modified ?homepage
    WHERE {
        ?vocab vann:preferredNamespacePrefix ?prefix .
        ?vocab dcterms:title ?name .
        OPTIONAL { ?vocab vann:preferredNamespaceUri ?uri_prefix . }
        OPTIONAL { ?vocab dcterms:description ?description . }
        OPTIONAL { ?vocab dcterms:modified ?modified . }
        OPTIONAL { ?vocab foaf:homepage ?homepage . }
    }
    ORDER BY ?vocab
"""
KEYWORD_SPARQL = """\
    SELECT ?vocab ?keyword
    WHERE { ?vocab dcat:keyword ?keyword . }
"""

columns = ["vocab", "name", "prefix", "uri_prefix", "description", "modified", "homepage"]


def get_lov(*, force_download: bool = False, force_refresh: bool = False):
    """Get the LOV data cloud registry."""
    if PROCESSED_PATH.exists() and not force_download and not force_refresh:
        return json.loads(PROCESSED_PATH.read_text())

    with tempfile.TemporaryDirectory() as dir:
        path = Path(dir).joinpath("lov.n3.gz")
        download(url=URL, path=path)
        graph = read_rdf(path)

    keywords = defaultdict(set)
    for vocab, keyword in graph.query(KEYWORD_SPARQL):
        keywords[str(vocab)].add(str(keyword))

    records = {}
    for result in graph.query(RECORD_SPARQL):
        d: Dict[str, Union[str, List[str]]] = {k: str(v) for k, v in zip(columns, result) if v}
        if k := keywords.get(str(result[0])):
            d["keywords"] = sorted(k)
        if "uri_prefix" in d:
            d["uri_prefix"] = d["uri_prefix"] + "$1"  # type:ignore
        if "homepage" in d:
            del d["vocab"]
        else:
            d["homepage"] = d.pop("vocab")
        records[d["prefix"]] = d

    PROCESSED_PATH.write_text(json.dumps(records, indent=2))
    return records


class LOVAligner(Aligner):
    """Aligner for LOV."""

    key = "lov"
    getter = get_lov
    curation_header = ("name", "homepage", "uri_prefix")


if __name__ == "__main__":
    LOVAligner.cli()
