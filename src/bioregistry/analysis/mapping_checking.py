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

from collections import defaultdict
from collections.abc import Mapping
from typing import Any

import pandas as pd
import tqdm
from sentence_transformers import SentenceTransformer
from sentence_transformers.util import cos_sim

from bioregistry import Resource, manager, read_mismatches, read_registry
from bioregistry.constants import EXPORT_ANALYSES
from bioregistry.external import GETTERS

OUTPUT_PATH = EXPORT_ANALYSES.joinpath("mapping_checking", "mapping_embedding_similarities.tsv")

#: see https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2
DEFAULT_MODEL = "all-MiniLM-L6-v2"
#: Metadata fields to use for embedding
METADATA_FIELDS = ["name", "description", "homepage"]


def get_scored_mappings_for_prefix(
    prefix: str,
    raw_entry: Resource,
    compiled_entry: Mapping[str, Any],
    model: SentenceTransformer,
    mismatch_entries: Mapping[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Return scored mappings for a given prefix."""
    # If no mappings at all then we don't need to do anything
    if not raw_entry.mappings and not mismatch_entries:
        return []

    # Collect all the mappings to process as tuples (better than dict since
    # the extra entries might contain the same registry as the raw entry
    # with a different prefix).
    mappings_to_process = []
    if raw_entry.mappings:
        mappings_to_process = [
            (mapped_registry, mapped_prefix, raw_entry.get_external(mapped_registry), 0)
            for mapped_registry, mapped_prefix in raw_entry.mappings.items()
        ]
    # Add any extra entries that were passed in
    if mismatch_entries:
        mappings_to_process.extend(
            (mapped_registry, mapped_entry["prefix"], mismatch_entries[mapped_registry], 1)
            for mapped_registry, mapped_entry in mismatch_entries.items()
        )

    # Define a reference metadata text by assuming that in the consensus registry
    # in exports, the name and description of the ontology are not completely
    # wrong and can serve as a reference point for comparison
    reference_text = " ".join([compiled_entry.get(part, "") for part in METADATA_FIELDS])

    mapping_entries = []
    for mapped_registry, mapped_prefix, details, known_mismatch in mappings_to_process:
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

        mapping_entries.append(
            {
                "prefix": prefix,
                "mapped_registry": mapped_registry,
                "mapped_prefix": mapped_prefix,
                "reference_text": reference_text,
                "external_text": mapping_text.replace("\n", " ").replace("  ", " "),
                "parts_used": ",".join(parts_used),
                "known_mismatch": known_mismatch,
            }
        )
    # Skip if we couldn't collect any useful mappings
    if not mapping_entries:
        return []

    # Compute embeddings for each mapping entry (in a single list but the
    # calculation is done individually)
    texts = [entry["external_text"] for entry in mapping_entries]
    embeddings = model.encode(texts, convert_to_tensor=True)
    # Calculate embedding for the reference text
    ref_embedding = model.encode(reference_text, convert_to_tensor=True)

    # Compute cosine similarities between the reference embedding and each
    # mapping's embedding.
    cosine_scores = cos_sim(ref_embedding, embeddings)[0].tolist()

    # Add similarity score and reference text to each entry in the mapping entries
    for entry, score in zip(mapping_entries, cosine_scores):
        entry["similarity"] = score

    return mapping_entries


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
                external_entry["prefix"] = external_prefix
                mismatch_entries[bioregistry_prefix][external_registry] = external_entry
    return dict(mismatch_entries)


def get_scored_mappings(model: SentenceTransformer) -> pd.DataFrame:
    """Return scored mappings for all prefixes."""
    # Read the raw registry and compile it
    raw_registry = read_registry()
    compiled_registry = manager.rasterize()

    # For benchmarking purposes, it is useful to include mappings that have already been curated as mismatches
    mismatch_entries = _get_mismatch_entries()

    all_mapping_entries = []
    # For each prefix, compute the similarity between the prefix's compiled
    # data and each applicable mapped prefix's data, then add these to
    # an aggregate list
    for prefix, compiled_entry in tqdm.tqdm(
        compiled_registry.items(), desc="Scoring prefix mappings"
    ):
        raw_entry = raw_registry[prefix]

        mapping_entries = get_scored_mappings_for_prefix(
            prefix, raw_entry, compiled_entry, model, mismatch_entries.get(prefix, {})
        )
        all_mapping_entries.extend(mapping_entries)

    # Collect all the similarities and metadata in a data frame
    # and sort so that first entry is most likely incorrect
    df = pd.DataFrame(all_mapping_entries)
    df_sorted = df.sort_values(by="similarity")
    return df_sorted


def _main() -> None:
    # Choose an embedding model
    model = SentenceTransformer(DEFAULT_MODEL)
    # Run mappings
    df = get_scored_mappings(model)
    df.round(9).to_csv(OUTPUT_PATH, index=False, sep="\t")


if __name__ == "__main__":
    _main()
