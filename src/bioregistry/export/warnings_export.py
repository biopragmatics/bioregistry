"""Generate the warnings file.

This lists any sorts of things that should be fixed upstream, but are instead manually
curated in the Bioregistry.
"""

from __future__ import annotations

from collections.abc import Callable

import click
import yaml
from tqdm import tqdm

from ..constants import DOCS_DATA, EXTERNAL
from ..parse_iri import parse_iri
from ..resolve import (
    get_example,
    get_external,
    get_homepage,
    get_name,
    get_pattern,
    get_provides_for,
    has_no_terms,
)
from ..resolve_identifier import get_iri
from ..schema_utils import read_metaregistry, read_registry
from ..uri_format import get_uri_format

__all__ = [
    "export_warnings",
]

CURATIONS_PATH = DOCS_DATA.joinpath("curation.yml")
WARNINGS_PATH = DOCS_DATA.joinpath("warnings.yml")


def _g(predicate: Callable[[str], bool]) -> list[dict[str, str | None]]:
    return [
        {
            "prefix": prefix,
            "name": get_name(prefix),
            "homepage": get_homepage(prefix),
        }
        for prefix in sorted(read_registry())
        if predicate(prefix)
    ]


def get_unparsable_uris() -> list[tuple[str, str, str]]:
    """Get a list of IRIs that can be constructed, but not parsed."""
    rows: list[tuple[str, str, str]] = []
    for prefix in tqdm(read_registry(), desc="Checking URIs"):
        example = get_example(prefix)
        if example is None:
            continue
        uri = get_iri(prefix, example, use_bioregistry_io=False)
        if uri is None:
            continue
        k, v = parse_iri(uri)
        if k is None or v is None:
            rows.append((prefix, example, uri))
    return rows


@click.command()
def export_warnings() -> None:
    """Make warnings list."""
    # unparsable = get_unparsable_uris()
    missing_wikidata_database = _g(
        lambda prefix: (
            (get_external(prefix, "wikidata") or {}).get("database") is None
            and not has_no_terms(prefix)
        )
    )
    missing_pattern = _g(lambda prefix: get_pattern(prefix) is None and not has_no_terms(prefix))
    missing_format_url = _g(
        lambda prefix: get_uri_format(prefix) is None and not has_no_terms(prefix)
    )
    missing_example = _g(
        lambda prefix: (
            get_example(prefix) is None
            and not has_no_terms(prefix)
            and get_provides_for(prefix) is None
        )
    )

    prefix_xrefs = [
        {
            "metaprefix": metaprefix,
            "name": registry.get_short_name(),
        }
        for metaprefix, registry in sorted(read_metaregistry().items())
        if EXTERNAL.joinpath(metaprefix, "curation.tsv").is_file()
    ]

    with CURATIONS_PATH.open("w") as file:
        yaml.safe_dump(
            {
                "wikidata": missing_wikidata_database,
                "pattern": missing_pattern,
                "formatter": missing_format_url,
                "example": missing_example,
                "prefix_xrefs": prefix_xrefs,
                # "unparsable": unparsable,
            },
            file,
        )

    miriam_pattern_wrong = [
        {
            "prefix": prefix,
            "name": get_name(prefix),
            "homepage": get_homepage(prefix),
            "correct": entry.pattern,
            "miriam": miriam_pattern,
        }
        for prefix, entry in read_registry().items()
        if entry.miriam
        and (miriam_pattern := entry.miriam.get("pattern")) is not None
        and entry.pattern
        and entry.pattern != miriam_pattern
    ]

    with WARNINGS_PATH.open("w") as file:
        yaml.safe_dump(
            {
                "wrong_patterns": miriam_pattern_wrong,
            },
            file,
        )


if __name__ == "__main__":
    export_warnings()
