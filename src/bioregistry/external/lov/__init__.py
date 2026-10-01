"""Download the LOV registry."""

from collections import defaultdict
from collections.abc import Iterable, Sequence
from pathlib import Path
from typing import ClassVar, cast

from pystow.utils import read_rdf

from bioregistry.alignment_model import Record, make_record
from bioregistry.constants import RAW_DIRECTORY
from bioregistry.external.alignment_utils import Aligner, build_getter

__all__ = [
    "LOVAligner",
    "get_lov",
]

DIRECTORY = Path(__file__).parent.resolve()
PROCESSED_PATH = DIRECTORY / "processed.json"
RAW_PATH = RAW_DIRECTORY.joinpath("lov.n3.gz")
URL = "https://lov.linkeddata.es/lov.n3.gz"

RECORD_SPARQL = """\
    SELECT ?vocab ?name ?prefix ?uri_prefix ?description ?homepage
    WHERE {
        ?vocab vann:preferredNamespacePrefix ?prefix .
        ?vocab dcterms:title ?name .
        OPTIONAL { ?vocab vann:preferredNamespaceUri ?uri_prefix . }
        OPTIONAL { ?vocab dcterms:description ?description . }
        OPTIONAL { ?vocab foaf:homepage ?homepage . }
    }
    ORDER BY ?vocab
"""
KEYWORD_SPARQL = """\
    SELECT ?vocab ?keyword
    WHERE { ?vocab dcat:keyword ?keyword . }
"""

columns = ["vocab", "name", "prefix", "uri_prefix", "description", "homepage"]


def process_lov(path: Path) -> dict[str, Record]:
    """Process LOV registry."""
    graph = read_rdf(path)
    keywords = defaultdict(set)
    for vocab, keyword in cast(Iterable[tuple[str, str]], graph.query(KEYWORD_SPARQL)):
        keywords[str(vocab)].add(str(keyword))

    records: dict[str, Record] = {}
    for result in cast(Iterable[tuple[str, ...]], graph.query(RECORD_SPARQL)):
        d: dict[str, str | list[str]] = {
            k: str(v) for k, v in zip(columns, result, strict=False) if v
        }
        if k := keywords.get(str(result[0])):
            d["keywords"] = sorted(k)
        if uri_prefix := d.pop("uri_prefix", None):
            d["uri_format"] = uri_prefix + "$1"  # type:ignore
        if "homepage" in d:
            del d["vocab"]
        else:
            d["homepage"] = d.pop("vocab")
        records[cast(str, d["prefix"])] = make_record(d)
    return records


get_lov = build_getter(
    processed_path=PROCESSED_PATH,
    raw_path=RAW_PATH,
    url=URL,
    func=process_lov,
)


class LOVAligner(Aligner):
    """Aligner for LOV."""

    key = "lov"
    getter = get_lov
    curation_header: ClassVar[Sequence[str]] = ("name", "homepage", "uri_format")


if __name__ == "__main__":
    LOVAligner.cli()
