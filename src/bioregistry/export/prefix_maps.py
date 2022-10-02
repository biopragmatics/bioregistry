# -*- coding: utf-8 -*-

"""Export the Bioregistry as a JSON-LD context."""

import json
from pathlib import Path
from textwrap import dedent
from typing import Mapping, Optional

import click

from bioregistry.constants import (
    CONTEXT_BIOREGISTRY_PATH,
    EXPORT_CONTEXTS,
    SHACL_TURTLE_PATH,
)
from bioregistry.resource_manager import manager

REVERSE_PREFIX_MAP_PATH = EXPORT_CONTEXTS.joinpath("reverse_prefix_map.json")


@click.command()
def generate_contexts():
    """Generate various context files."""
    reverse_prefix_map = manager.get_reverse_prefix_map(include_prefixes=True, strict=False)
    REVERSE_PREFIX_MAP_PATH.write_text(json.dumps(reverse_prefix_map, indent=4, sort_keys=True))

    _context_prefix_maps()
    _collection_prefix_maps()

    prefix_map = manager.get_prefix_map()
    pattern_map = manager.get_pattern_map()
    _write_prefix_map(CONTEXT_BIOREGISTRY_PATH, prefix_map=prefix_map)
    _write_shacl(SHACL_TURTLE_PATH, prefix_map=prefix_map, pattern_map=pattern_map)


def _collection_prefix_maps():
    for collection in manager.collections.values():
        name = collection.context
        if name is None:
            continue
        path_stub = EXPORT_CONTEXTS.joinpath(name)
        prefix_map = collection.as_prefix_map()
        pattern_map = manager.get_pattern_map()
        _write_prefix_map(path_stub.with_suffix(".context.jsonld"), prefix_map=prefix_map)
        _write_shacl(
            path_stub.with_suffix(".context.ttl"), prefix_map=prefix_map, pattern_map=pattern_map
        )


def _context_prefix_maps():
    for key in manager.contexts:
        prefix_map, pattern_map = manager.get_context_artifacts(key)
        stub = EXPORT_CONTEXTS.joinpath(key)
        _write_prefix_map(stub.with_suffix(".context.jsonld"), prefix_map=prefix_map)
        _write_shacl(
            stub.with_suffix(".context.ttl"), prefix_map=prefix_map, pattern_map=pattern_map
        )

        if key == "obo":  # Special case, maybe put this in data model
            prefix_map, pattern_map = manager.get_context_artifacts(key, include_synonyms=True)
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


if __name__ == "__main__":
    generate_contexts()
