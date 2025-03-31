---
layout: page
title: Semi-automated Review of Cross-registry Mappings
permalink: /curation/mappings
---

The Bioregistry is a metaregistry of identifiers resources, meaning that it
harmonizes across entries of multiple external registries via **mappings**. Each
mapping is between a Bioregistry prefix and a specific prefix within one of the
external registries the Bioregistry integrtes with. The initial creation of such
mappings is largely automated. The vast majority of these mappings is correct
but some correspond to prefixes that do not represent the same resource (or more
specifically, the same semantic space) and should therefore not be mapped to
each other.

The following
[TSV file](https://github.com/biopragmatics/bioregistry/blob/main/src/bioregistry/data/curated_mappings.sssom.tsv)
contains mappings reviewed by curators. This file follows the
[SSSOM standard](https://mapping-commons.github.io/sssom/), a community standard
for sharing semantic mappings. When reviewing a mapping, curators should update
the TSV file with the following information:

- `subject_id`: The CURIE corresponding to Bioregistry prefix from which this is
  a mapping. Even when a mapping is symmetric, as a convention, this should
  always be the Bioregistry prefix not the external one.
- `predicate_modifier`: A modifier on the predicate, typically `Not` if the
  mapping is negative.
- `predicate_id`: The CURIE representing the predicate of the mapping, for
  instance `skos:exactMatch`.
- `object_id`: The CURIE corresponding to the external prefix to which this is a
  mapping.
- `creator_id`: The ORCID of the curator reviewing the mapping represented as a
  CURIE.
- `mapping_justification`: A CURIE representing how the mapping was created,
  typically `semapv:ManualMappingCuration` for manual curation.
- `comment`: Any additional notes or comments regarding the mapping that was
  reviewed.

The Bioregistry uses a machine learning-based approach to automatically identify
semantic similarity between the metadata associated with the Bioregistry entry
and the external registry entry connected by a mapping. The resulting similarity
scores are available in
[this TSV file](https://github.com/biopragmatics/bioregistry/blob/main/exports/analyses/mapping_checking/mapping_embedding_similarities.tsv).
Curation can be prioritized to entries in this file that have low similarity
scores but have not been curated yet.
