"""Generate the warnings file.

This lists any sorts of things that should be fixed upstream, but are instead manually
curated in the Bioregistry.
"""

from __future__ import annotations

import os
from collections.abc import Callable

import click
import yaml
from tqdm import tqdm

import bioregistry
from bioregistry import parse_iri

from ..constants import DOCS_DATA, EXTERNAL
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

ENTRIES = sorted(
    (prefix, resource.model_dump(exclude_none=True)) for prefix, resource in read_registry().items()
)


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
        lambda prefix: get_external(prefix, "wikidata").get("database") is None
        and not has_no_terms(prefix)
    )
    missing_pattern = _g(lambda prefix: get_pattern(prefix) is None and not has_no_terms(prefix))
    missing_format_url = _g(
        lambda prefix: get_uri_format(prefix) is None and not has_no_terms(prefix)
    )
    missing_example = _g(
        lambda prefix: get_example(prefix) is None
        and not has_no_terms(prefix)
        and get_provides_for(prefix) is None
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
            "correct": entry["pattern"],
            "miriam": entry["miriam"]["pattern"],
        }
        for prefix, entry in ENTRIES
        if "miriam" in entry
        and "pattern" in entry
        and entry["pattern"] != entry["miriam"]["pattern"]
    ]

    miriam_embedding_rewrites = [
        {
            "prefix": prefix,
            "name": get_name(prefix),
            "homepage": get_homepage(prefix),
            "pattern": get_pattern(prefix),
            "correct": entry["namespace.embedded"],
            "miriam": entry["miriam"]["namespaceEmbeddedInLui"],
        }
        for prefix, entry in ENTRIES
        if "namespace.embedded" in entry
    ]

    # When are namespace rewrites required?
    miriam_prefix_rewrites = [
        {
            "prefix": prefix,
            "name": get_name(prefix),
            "homepage": get_homepage(prefix),
            "pattern": get_pattern(prefix),
            "correct": entry["namespace.rewrite"],
        }
        for prefix, entry in ENTRIES
        if "namespace.rewrite" in entry
    ]

    with open(os.path.join(DOCS_DATA, "warnings.yml"), "w") as file:
        yaml.safe_dump(
            {
                "wrong_patterns": miriam_pattern_wrong,
                "embedding_rewrites": miriam_embedding_rewrites,
                "prefix_rewrites": miriam_prefix_rewrites,
                "license_conflict": [
                    {"prefix": prefix, "obo": obo, "ols": ols}
                    for prefix, _override, obo, ols in bioregistry.get_license_conflicts()
                ],
            },
            file,
        )


if __name__ == "__main__":
    export_warnings()
