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

Detect potentially incorrect mappings by comparing embeddings of bioregistry entry metadata
against the metadata corresponding to mapped prefixes. Low similarity scores indicate a potential
false positive mapping that can be reviewed manually and removed if confirmed to be incorrect.

Run with either of the following commands:

1. ``uv run --script mapping_checking.py``
2. ``python -m bioregistry.analysis.mapping_checking``
3. ``tox -e mapping-checking``
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import pandas as pd
import tqdm
from sentence_transformers import SentenceTransformer
from sentence_transformers.util import cos_sim

from bioregistry import Resource, manager, read_registry
from bioregistry.constants import EXPORT_ANALYSES

OUTPUT_PATH = EXPORT_ANALYSES.joinpath("mapping_checking", "mapping_embedding_similarities.tsv")

#: see https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2
DEFAULT_MODEL = "all-MiniLM-L6-v2"


def get_scored_mappings_for_prefix(
    prefix: str, raw_entry: Resource, compiled_entry: Mapping[str, Any], model: SentenceTransformer
) -> list[dict[str, Any]]:
    """Return scored mappings for a given prefix."""
    # If not mappings at all then we don't need to do anything
    if not raw_entry.mappings:
        return []

    mapping_entries = []
    for mapped_registry, mapped_prefix in raw_entry.mappings.items():
        details = raw_entry.get_external(mapped_registry)
        # In a handful of cases, an entry in the mappings dict doesn't correspond
        # to an actual key to provide additional data on the mapping
        if not details:
            continue

        text_parts = []
        parts_used = []
        # Combine fields that are likely useful for an embedding
        for field in ["name", "description", "homepage", "uri_format"]:
            if field in details:
                text_parts.append(str(details[field]))
                parts_used.append(field)
        # Skip if no details available at all
        if not text_parts:
            continue
        # Skip if only the URI format is available since this alone
        # is not generally useful
        if len(parts_used) == 1 and parts_used[0] == "uri_format":
            continue
        mapping_text = " ".join(text_parts)

        mapping_entries.append(
            {
                "prefix": prefix,
                "mapped_registry": mapped_registry,
                "mapped_prefix": mapped_prefix,
                "text": mapping_text.replace("\n", " ").replace("  ", " "),
                "parts_used": ",".join(parts_used),
            }
        )
    # Skip if we couldn't collect any useful mappings
    if not mapping_entries:
        return []

    # Compute embeddings for each mapping entry (in a single list but the
    # calculation is done individually)
    texts = [entry["text"] for entry in mapping_entries]
    embeddings = model.encode(texts, convert_to_tensor=True)

    # Define a reference embedding by assuming that in the consensus registry
    # in exports, the name and description of the ontology are not completely
    # wrong and can serve as a reference point for comparison
    reference_text = " ".join(
        [prefix, compiled_entry.get("name", ""), compiled_entry.get("description", "")]
    )
    ref_embedding = model.encode(reference_text, convert_to_tensor=True)

    # Compute cosine similarities between the reference embedding and each
    # mapping's embedding.
    cosine_scores = cos_sim(ref_embedding, embeddings)[0].tolist()

    # Add similarity score to each entry in the mapping entries
    for entry, score in zip(mapping_entries, cosine_scores):
        entry["similarity"] = score

    return mapping_entries


def get_scored_mappings(model: SentenceTransformer) -> pd.DataFrame:
    """Return scored mappings for all prefixes."""
    # Read the raw registry and compile it
    raw_registry = read_registry()
    compiled_registry = manager.rasterize()

    all_mapping_entries = []
    # For each prefix, compute the similarity between the prefix's compiled
    # data and each applicable mapped prefix's data, then add these to
    # an aggregate list
    for prefix, compiled_entry in tqdm.tqdm(
        compiled_registry.items(), desc="Scoring prefix mappings"
    ):
        raw_entry = raw_registry[prefix]
        mapping_entries = get_scored_mappings_for_prefix(prefix, raw_entry, compiled_entry, model)
        all_mapping_entries.extend(mapping_entries)

    # Collect all the similarities and metadata in a data frame
    # and sort so that first entry is most likely incorrect
    df = pd.DataFrame(all_mapping_entries)
    df_sorted = df.sort_values(by="similarity")
    return df_sorted


def _main():
    # Choose an embedding model
    model = SentenceTransformer(DEFAULT_MODEL)
    # Run mappings
    df = get_scored_mappings(model)
    df.round(9).to_csv(OUTPUT_PATH, index=False, sep="\t")


if __name__ == "__main__":
    _main()
