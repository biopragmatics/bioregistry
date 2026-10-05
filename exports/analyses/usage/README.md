# Usage Analysis

Files:

- [`results-raw.tsv`](results-raw.tsv): A two-column file with prefixes for
  ontologies, controlled vocabularies, and other related artifacts and prefixes
  for the resources that they use
- [`errors.tsv](errors.tsv): A file with errors that occurred during
  construction of the raw results file
- [`results-closure.tsv`](results-closure.tsv): A processed version of the raw
  results where the transitive closure has been applied to explicitly enumerate
  all indirect dependencies in addition to the direct ones.
