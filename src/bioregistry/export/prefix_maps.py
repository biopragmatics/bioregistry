# -*- coding: utf-8 -*-

"""Export the Bioregistry as a JSON-LD context."""

import json
from collections import ChainMap
from pathlib import Path
from textwrap import dedent
from typing import Mapping, Optional, Tuple

import click

import bioregistry
from bioregistry import get_pattern_map, get_prefix_map
from bioregistry.constants import (
    CONTEXT_BIOREGISTRY_PATH,
    EXPORT_CONTEXTS,
    SHACL_TURTLE_PATH,
)
from bioregistry.schema import Collection


@click.command()
def generate_contexts():
    """Generate various context files."""
    _context_prefix_maps()
    _collection_prefix_maps()

    prefix_map = get_prefix_map()
    pattern_map = get_pattern_map()
    _write_prefix_map(CONTEXT_BIOREGISTRY_PATH, prefix_map=prefix_map)
    _write_shacl(SHACL_TURTLE_PATH, prefix_map=prefix_map, pattern_map=pattern_map)


def _collection_prefix_maps():
    for collection in bioregistry.read_collections().values():
        name = collection.context
        if name is None:
            continue
        path_stub = EXPORT_CONTEXTS.joinpath(name)
        prefix_map = collection.as_prefix_map()
        pattern_map = get_pattern_map()
        _write_prefix_map(path_stub.with_suffix(".context.jsonld"), prefix_map=prefix_map)
        _write_shacl(
            path_stub.with_suffix(".context.ttl"), prefix_map=prefix_map, pattern_map=pattern_map
        )


def get_prescriptive_artifacts(
    key: str, include_synonyms: Optional[bool] = None
) -> Tuple[Mapping[str, str], Mapping[str, str]]:
    """Get a prescriptive prefix map."""
    context = bioregistry.get_context(key)
    if context is None:
        raise KeyError
    remapping = dict(
        ChainMap(
            *(
                bioregistry.get_registry_map(metaprefix)
                for metaprefix in context.prefix_priority or []
            ),
            context.prefix_remapping or {},
        )
    )
    include_synonyms = (
        include_synonyms if include_synonyms is not None else context.include_synonyms
    )
    prescriptive_prefix_map = get_prefix_map(
        remapping=remapping,
        priority=context.uri_prefix_priority,
        include_synonyms=include_synonyms,
        use_preferred=context.use_preferred,
    )
    prescriptive_pattern_map = get_pattern_map(
        remapping=remapping,
        include_synonyms=include_synonyms,
        use_preferred=context.use_preferred,
    )
    return prescriptive_prefix_map, prescriptive_pattern_map


def _context_prefix_maps():
    for key in bioregistry.read_contexts():
        prefix_map, pattern_map = get_prescriptive_artifacts(key)
        stub = EXPORT_CONTEXTS.joinpath(key)
        _write_prefix_map(stub.with_suffix(".context.jsonld"), prefix_map=prefix_map)
        _write_shacl(
            stub.with_suffix(".context.ttl"), prefix_map=prefix_map, pattern_map=pattern_map
        )

        if key == "obo":  # Special case, maybe put this in data model
            prefix_map, pattern_map = get_prescriptive_artifacts(key, include_synonyms=True)
            stub_double = EXPORT_CONTEXTS.joinpath(f"{key}_synonyms")
            _write_prefix_map(stub_double.with_suffix(".context.jsonld"), prefix_map=prefix_map)
            _write_shacl(
                stub_double.with_suffix(".context.ttl"),
                prefix_map=prefix_map,
                pattern_map=pattern_map,
            )


def _write_shacl(
    path: Path, *, prefix_map: Mapping[str, str], pattern_map: Optional[Mapping[str, str]] = None
) -> None:
    text = dedent(
        """\
        @prefix sh: <http://www.w3.org/ns/shacl#> .

        [
          sh:declare
        {entries}
        ] .
        """
    )
    entries = ",\n".join(
        f'    [ sh:prefix "{prefix}" ; sh:namespace "{uri_prefix}" ]'
        if not pattern_map or prefix not in pattern_map
        else f'    [ sh:prefix "{prefix}" ; sh:namespace "{uri_prefix}" ; sh:pattern "{pattern_map[prefix]}" ]'
        for prefix, uri_prefix in sorted(prefix_map.items())
    )
    path.write_text(text.format(entries=entries))


def _write_prefix_map(path: Path, *, prefix_map: Mapping[str, str]) -> None:
    with path.open("w") as file:
        json.dump(
            fp=file,
            indent=4,
            sort_keys=True,
            obj={
                "@context": prefix_map,
            },
        )


def collection_to_context_jsonlds(collection: Collection) -> str:
    """Get the JSON-LD context as a string from a given collection."""
    return json.dumps(collection.as_context_jsonld())


def get_obofoundry_prefix_map(include_synonyms: bool = False) -> Mapping[str, str]:
    """Get the OBO Foundry prefix map.

    :param include_synonyms: Should synonyms of each prefix also be included as additional prefixes, but with
        the same URL prefix?
    :return: A mapping from prefixes to prefix URLs.
    """
    return get_prescriptive_artifacts("obo")[0]


if __name__ == "__main__":
    generate_contexts()
