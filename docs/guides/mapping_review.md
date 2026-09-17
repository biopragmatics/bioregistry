---
layout: page
title: Mapping to External Registries
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

## Semi-automated Review of Cross-registry Mappings

The Bioregistry uses a machine learning-based approach to automatically identify
semantic similarity between the metadata associated with the Bioregistry entry
and the external registry entry connected by a mapping. The resulting similarity
scores are available in
[this TSV file](https://github.com/biopragmatics/bioregistry/blob/main/exports/analyses/mapping_checking/mapping_embedding_similarities.tsv).
Curation can be prioritized to entries in this file that have low similarity
scores but have not been curated yet.

## Curating Mappings to Providers in External Registries

The Bioregistry ingest and harmonizes 30+ external registries that contain
metadata describing ontologies, databases, and other resources that mint
semantic spaces.

Some registries, such as the
[UniProt Database](https://bioregistry.io/uniprot.resource) registry, contain
many records for databases that use UniProt IDs, but aren't the UniProt resource
themselves. The Bioregistry currently does not have a mechanism for ingesting
this information, but for some applications, it's useful to have.

These can be curated in the `curated_mappings.sssom.tsv` SSSOM file using the
[has provider (bioregistry.schema:0000030)](https://bioregistry.io/schema/#0000030)
predicate. For example, `bioregistry:uniprot` has the provider
`uniprot:DB-0262`, which corresponds to the AlphaFoldDB.
