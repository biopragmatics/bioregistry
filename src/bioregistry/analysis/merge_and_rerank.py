"""Merges and reranks new/uncurated papers."""

import sys

import pandas as pd

curated_file = sys.argv[1]
new_file = sys.argv[2]
output_file = sys.argv[3]

curated_df = pd.read_csv(curated_file)

new_df = pd.read_csv(new_file, delimiter="\t", names=["pmid", "title", "score"])

merged_df = pd.concat([curated_df, new_df], ignore_index=True)

merged_df = merged_df.sort_values("score", ascending=False).drop_duplicates("pmid")

merged_df.to_csv(output_file, index=False)
