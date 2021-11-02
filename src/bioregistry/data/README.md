# Bioregisty Data

This is the folder that holds the manually curated, single source of truth JSON
files that power the Bioregistry. It also has a directory `external/`
where the processed content from external registries gets stored.

## Main Database Files

### [`bioregistry.json`](bioregistry.json)

This is the main file that supports the Bioregistry's registry. It has three
goals:

1. Support novel curation
2. Support import and alignment of prefixes and metadata from external
   registries
3. Enable overriding of metadata from external registries when they are wrong

All edits to the registry should be made through this file. However, you'll
notice that for some entries, there are not top-level fields like "name". This
is because the associated Python package for the Bioregistry has logic baked in
for accessing metadata through the mapped registries. This reduces the curation
burden and enables the Bioregistry to benefit from upstream changes in external
registries.

Several exports to YAML, TSV, and RDF, including consensus views over the
registry, are built on a nightly basis and can be downloaded via the
[`exports/`](https://github.com/biopragmatics/bioregistry/tree/main/exports)
directory.

### [`collections.json`](collections.json)

### [`metaregistry.json`](metaregistry.json)

### [`mismatch.json`](metaregistry.json)

## Processing Help Files

### [`processing_biolink.json`](processing_biolink.json)

### [`processing_go.json`](processing_go.json)

### [`processing_ols.json`](processing_ols.json)

### [`processing_wikidata.json`](processing_wikidata.json)
