# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "bioregistry[mapping-checking]",
# ]
#
# [tool.uv.sources]
# bioregistry = { path = "../../..", editable = true  }
# ///

"""Run the mapping checking workflow.

Detect potentially incorrect mappings by comparing embeddings of bioregistry entry
metadata against the metadata corresponding to mapped prefixes. Low similarity scores
indicate a potential false positive mapping that can be reviewed manually and removed if
confirmed to be incorrect.

Run with either of the following commands:

1. ``uv run --script mapping_checking.py``
2. ``python -m bioregistry.analysis.mapping_checking``
3. ``tox -e mapping-checking``
"""

from __future__ import annotations

import itertools as itt
from collections import defaultdict
from collections.abc import Mapping
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

import click
import pystow
import sssom_pydantic
import tqdm
from curies import NamableReference
from curies.vocabulary import exact_match, lexical_matching_process
from sentence_transformers.util import cos_sim
from sssom_pydantic import ExtensionDefinition, MappingSet, SemanticMapping, Slot

import bioregistry
from bioregistry import Resource, manager, read_mismatches, read_registry
from bioregistry.constants import EXPORT_ANALYSES
from bioregistry.external import GETTERS
from bioregistry.schema.struct import Record

if TYPE_CHECKING:
    from sentence_transformers import SentenceTransformer

OUTPUT_PATH = EXPORT_ANALYSES.joinpath("mapping_checking", "mapping_embedding_similarities.tsv")

#: Metadata fields to use for embedding
METADATA_FIELDS = ["name", "description", "homepage"]

METADATA = MappingSet(
    id="https://github.com/biopragmatics/bioregistry/raw/refs/heads/main/exports/analyses/mapping_checking/mapping_embedding_similarities.tsv",
    title="Bioregistry Mapping Similarity Analysis",
    license="https://creativecommons.org/publicdomain/zero/1.0/",
    issue_tracker="https://github.com/biopragmatics/bioregistry/issues",
    extension_definitions=[
        ExtensionDefinition.default("parts_used"),
        ExtensionDefinition.default("reference_text"),
        ExtensionDefinition.default("mapping_text"),
    ],
)


def get_scored_mappings_for_prefix(
    prefix: str,
    resource: Resource,
    compiled_entry: Mapping[str, Any],
    model: SentenceTransformer,
    mismatch_entries_dict: dict[str, Mapping[str, Any]] | None = None,
    precision: int | None = None,
) -> list[SemanticMapping]:
    """Return scored mappings for a given prefix."""
    mismatch_entries = (mismatch_entries_dict or {}).get(prefix, {})

    # If no mappings at all then we don't need to do anything
    if not resource.mappings and (mismatch_entries_dict is None or not mismatch_entries):
        return []

    if precision is None:
        precision = 9

    # Collect all the mappings to process as tuples (better than dict since
    # the extra entries might contain the same registry as the raw entry
    # with a different prefix).
    mappings_to_process: list[tuple[str, str, Record | None, int]] = []
    if resource.mappings:
        mappings_to_process.extend(
            (external_registry, external_prefix, resource.get_external(external_registry), 0)
            for external_registry, external_prefix in resource.mappings.items()
        )

    # Add mismatches if benchmarking mode is on
    if mismatch_entries_dict is not None:
        mappings_to_process.extend(
            (mapped_registry, mapped_entry["prefix"], mapped_entry, 1)
            for mapped_registry, mapped_entry in mismatch_entries.items()
        )

    # Define a reference metadata text by assuming that in the consensus registry
    # in exports, the name and description of the ontology are not completely
    # wrong and can serve as a reference point for comparison
    reference_text = _clean(" ".join([compiled_entry.get(part, "") for part in METADATA_FIELDS]))

    mappings: list[SemanticMapping] = []
    for external_registry, external_prefix, details, known_mismatch in mappings_to_process:
        # In a handful of cases, an entry in the mappings dict doesn't correspond
        # to an actual key to provide additional data on the mapping
        if not details:
            continue

        text_parts = []
        parts_used = []
        # Combine fields that are likely useful for an embedding
        for field in METADATA_FIELDS:
            if field in details:
                text_parts.append(str(details[field]))
                parts_used.append(field)
        # Skip if no details available at all
        if not text_parts:
            continue
        mapping_text = " ".join(text_parts)
        mappings.append(
            SemanticMapping(
                subject=NamableReference(
                    prefix="bioregistry", identifier=prefix, name=resource.get_name()
                ),
                predicate=exact_match,
                object=NamableReference(
                    prefix=external_registry,
                    identifier=external_prefix,
                    name=resource._get_external_value(external_registry, "name"),
                ),
                justification=lexical_matching_process,
                comment=f"{known_mismatch=}" if mismatch_entries_dict is not None else None,
                extensions={
                    "parts_used": Slot.default("parts_used", ",".join(parts_used)),
                    "reference_text": Slot.default("reference_text", reference_text),
                    "mapping_text": Slot.default("mapping_text", _clean(mapping_text)),
                },
            )
        )
    # Skip if we couldn't collect any useful mappings
    if not mappings:
        return []

    # Compute embeddings for each mapping entry (in a single list but the
    # calculation is done individually)
    texts = [
        cast(str, mapping.extensions["mapping_text"].value) if mapping.extensions else ""
        for mapping in mappings
    ]
    embeddings = model.encode(texts, convert_to_tensor=True)
    # Calculate embedding for the reference text
    ref_embedding = model.encode(reference_text, convert_to_tensor=True)

    # Compute cosine similarities between the reference embedding and each
    # mapping's embedding.
    cosine_scores = cos_sim(ref_embedding, embeddings)
    # linearly map range from [-1,1] to [0,1]
    cosine_scores = (cosine_scores + 1.0) / 2.0
    cc = cosine_scores.clip(-1.0, 1.0)[0].tolist()

    # Add similarity score to each entry in the mapping entries
    mappings = [
        entry.model_copy(update={"similarity_score": round(score, precision)})
        for entry, score in zip(mappings, cc, strict=True)
    ]

    return mappings


def _clean(s: str) -> str:
    return s.replace("\r\n", " ").replace("\n", " ").replace("  ", " ")


def _get_mismatch_entries() -> dict[str, Any]:
    """Return a dictionary of entries corresponding to known mismatches."""
    external_registries = {}
    # Get functions to read processed external registry content
    external_getters = {
        external_registry: getter_fun for external_registry, _, getter_fun in GETTERS
    }
    # Read in all the known curated mismatches
    mismatches = read_mismatches()
    # For all the curated mismatches, read the external registry involved
    # and extract the part relevant for the curated mismatch, then add it to
    # the raw registry for scoring
    mismatch_entries: defaultdict[str, dict[str, Any]] = defaultdict(dict)
    # We compile content from external registries directly to be able
    # to access known mismatches that are otherwise not propagated to the
    # bioregistry
    for bioregistry_prefix, mismatch_data in mismatches.items():
        for external_registry, external_prefixes in mismatch_data.items():
            for external_prefix in external_prefixes:
                if external_registry not in external_registries:
                    external_registries[external_registry] = external_getters[external_registry](
                        force_download=False
                    )
                external_entry = external_registries[external_registry].get(external_prefix)
                if not external_entry:
                    continue
                mismatch_entries[bioregistry_prefix][external_registry] = {
                    "prefix": external_prefix,
                    **external_entry.model_dump(),
                }
    return dict(mismatch_entries)


def get_scored_mappings(
    model: SentenceTransformer | None = None,
    *,
    precision: int | None = None,
    benchmarking: bool = True,
) -> list[SemanticMapping]:
    """Return scored mappings for all prefixes."""
    model = pystow.get_sentence_transformer(model)

    # Read the raw registry and compile it
    raw_registry = read_registry()
    compiled_registry = manager.rasterize()

    if benchmarking:
        # For benchmarking purposes, it is useful to include mappings that have already been curated as mismatches
        mismatch_entries = _get_mismatch_entries()
    else:
        mismatch_entries = None

    # For each prefix, compute the similarity between the prefix's compiled
    # data and each applicable mapped prefix's data, then add these to
    # an aggregate list
    mappings = list(
        itt.chain.from_iterable(
            get_scored_mappings_for_prefix(
                prefix,
                raw_registry[prefix],
                compiled_entry,
                model,
                mismatch_entries_dict=mismatch_entries,
                precision=precision,
            )
            for prefix, compiled_entry in tqdm.tqdm(
                compiled_registry.items(),
                desc="Scoring prefix mappings",
                unit_scale=True,
                unit="record",
            )
        )
    )
    return mappings


@click.command()
@click.option("-o", "--output", type=Path, default=OUTPUT_PATH)
@click.option("--benchmarking", is_flag=True)
def main(output: Path, benchmarking: bool) -> None:
    """Run mapping checking analysis."""
    mappings = get_scored_mappings(benchmarking=benchmarking)
    mappings = sorted(mappings, key=lambda mapping: mapping.similarity_score or 0.0)
    converter = bioregistry.get_preferred_converter()
    sssom_pydantic.write(
        mappings,
        output,
        metadata=METADATA,
        converter=converter,
        exclude_columns={"predicate_label"},
    )


if __name__ == "__main__":
    main()
