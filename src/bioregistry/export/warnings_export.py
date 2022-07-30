# -*- coding: utf-8 -*-

"""Generate the warnings file.

This lists any sorts of things that should be fixed upstream, but are instead manually curated in the Bioregistry.
"""

import os
from typing import Callable

import click
import yaml
from tqdm import tqdm

import bioregistry
from bioregistry.constants import DOCS_DATA, EXTERNAL
from bioregistry.resolve import get_external

__all__ = [
    "export_warnings",
]

CURATIONS_PATH = DOCS_DATA.joinpath("curation.yml")

ENTRIES = sorted(
    (prefix, resource.dict(exclude_none=True))
    for prefix, resource in bioregistry.read_registry().items()
)


def _g(predicate: Callable[[str], bool]):
    return [
        {
            "prefix": prefix,
            "name": bioregistry.get_name(prefix),
            "homepage": bioregistry.get_homepage(prefix),
        }
        for prefix in sorted(bioregistry.read_registry())
        if predicate(prefix)
    ]


def get_unparsable_uris():
    """Get a list of IRIs that can be constructed, but not parsed."""
    rows = []
    for prefix in tqdm(bioregistry.read_registry(), desc="Checking URIs"):
        example = bioregistry.get_example(prefix)
        if example is None:
            continue
        uri = bioregistry.get_iri(prefix, example, use_bioregistry_io=False)
        if uri is None:
            continue
        k, v = bioregistry.parse_iri(uri)
        if k is None:
            rows.append((prefix, example, uri, k, v))
    return rows


@click.command()
def export_warnings():
    """Make warnings list."""
    # unparsable = get_unparsable_uris()
    missing_wikidata_database = _g(
        lambda prefix: get_external(prefix, "wikidata").get("database") is None
    )
    missing_pattern = _g(lambda prefix: bioregistry.get_pattern(prefix) is None)
    missing_format_url = _g(lambda prefix: bioregistry.get_uri_format(prefix) is None)
    missing_example = _g(
        lambda prefix: bioregistry.get_example(prefix) is None
        and not bioregistry.has_no_terms(prefix)
        and bioregistry.get_provides_for(prefix) is None
    )

    prefix_xrefs = [
        {
            "metaprefix": metaprefix,
            "name": registry.get_short_name(),
        }
        for metaprefix, registry in sorted(bioregistry.read_metaregistry().items())
        if EXTERNAL.joinpath(metaprefix, "curation.tsv").is_file()
    ]

    with CURATIONS_PATH.open("w") as file:
        yaml.safe_dump(
            {
                "wikidata": missing_wikidata_database,
                "pattern": missing_pattern,
                "formatter": missing_format_url,
                "example": missing_example,
                "prefix_xrefs": prefix_xrefs
                # "unparsable": unparsable,
            },
            file,
        )

    miriam_pattern_wrong = [
        dict(
            prefix=prefix,
            name=bioregistry.get_name(prefix),
            homepage=bioregistry.get_homepage(prefix),
            correct=entry["pattern"],
            miriam=entry["miriam"]["pattern"],
        )
        for prefix, entry in ENTRIES
        if "miriam" in entry
        and "pattern" in entry
        and entry["pattern"] != entry["miriam"]["pattern"]
    ]

    miriam_embedding_rewrites = [
        dict(
            prefix=prefix,
            name=bioregistry.get_name(prefix),
            homepage=bioregistry.get_homepage(prefix),
            pattern=bioregistry.get_pattern(prefix),
            correct=entry["namespace.embedded"],
            miriam=entry["miriam"]["namespaceEmbeddedInLui"],
        )
        for prefix, entry in ENTRIES
        if "namespace.embedded" in entry
    ]

    # When are namespace rewrites required?
    miriam_prefix_rewrites = [
        dict(
            prefix=prefix,
            name=bioregistry.get_name(prefix),
            homepage=bioregistry.get_homepage(prefix),
            pattern=bioregistry.get_pattern(prefix),
            correct=entry["namespace.rewrite"],
        )
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
                    dict(prefix=prefix, obo=obo, ols=ols)
                    for prefix, _override, obo, ols in bioregistry.get_license_conflicts()
                ],
            },
            file,
        )


if __name__ == "__main__":
    export_warnings()
