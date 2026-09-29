# Embeddings-based checking of mapped prefixes

![](mapping_checking_workflow.png)

This workflow outputs predicted mappings in the
[Simple Standard for Sharing Ontological Mappings (SSSOM)](https://mapping-commons.github.io/sssom/dev/)
format in
[`mapping_embedding_similarities.sssom.tsv`](mapping_embedding_similarities.sssom.tsv).

The columns of this file are as follows:

- `subject_id`: a CURIE representing Bioregistry prefix from which this is a
  mapping.
- `subject_label`: the name of the resource in the Bioregistry
- `predicate_id`: always `skos:exactMatch`
- `object_id`: a CURIE representing the prefix in the external registry
- `object_label`: the name of the resource in the external registry
- `mapping_justification`: always `semapv:LexicalMatching`
- `similarity_score`: The similarity score between 0 and 1 (due to numerical
  accuracy score is sometimes outside these ranges by a very small margin).
- `parts_used`: The metadata fields that were used (depending on availability)
  to construct the external text.
- `reference_text`: The concatenated metadata text from the Bioregistry
  consensus, serving as reference.
- `mapping_text`: The concatenated metadata text from the external registry.
