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
[TSV file](https://github.com/biopragmatics/bioregistry/blob/main/src/bioregistry/data/curated_mappings.tsv)
contains mappings reviewed by curators. When reviewing a mapping, curators
should update the TSV file with the following information:

- `prefix`: The Bioregistry prefix from which this is a mapping.
- `mapped_registry`: The external registry to which this is a mapping.
- `mapped_prefix`: The external registry's prefix to which this is a mapping.
- `correct`: 1 if this is a correct mappings and 0 otherwise.
- `orcid`: The ORCID of the curator reviewing the mapping.
- `notes`: Any additional notes or comments regarding the mapping that was
  reviewed.

The Bioregistry uses a machine learning-based approach to automatically identify
semantic similarity between the metadata associated with the Bioregistry entry
and the external registry entry connected by a mapping. The resulting similarity
scores are available in
[this TSV file](https://github.com/biopragmatics/bioregistry/blob/main/exports/analyses/mapping_checking/mapping_embedding_similarities.tsv).
Curation can be prioritized to entries in this file that have low similarity
scores but have not been curated yet.
