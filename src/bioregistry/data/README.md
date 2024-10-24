# Bioregisty Data

This is the folder that holds the manually curated, single source of truth JSON
files that power the Bioregistry. It also has a directory `external/` where the
processed content from external registries gets stored.

## Main Database Files

### [`bioregistry.json`](bioregistry.json)

This is the main file that supports the Bioregistry's registry. It has three
goals:

1. Support novel curation
2. Support import and alignment of prefixes and metadata from external
   registries
3. Enable overriding of metadata from external registries when they are wrong

All edits to the registry should be made through this file. However, you'll
notice that for some entries, there are no top-level fields like "name". This is
because the associated Python package for the Bioregistry has logic baked in for
accessing metadata through the mapped registries. This reduces the curation
burden and enables the Bioregistry to benefit from upstream changes in external
registries.

Several exports to YAML, TSV, and RDF, including consensus views over the
registry, are built on a weekly basis and can be downloaded via the
[`exports/`](https://github.com/biopragmatics/bioregistry/tree/main/exports)
directory.

### [`metaregistry.json`](metaregistry.json)

The metaregistry contains information about external registries.

### [`collections.json`](collections.json)

This file contains manually curated collections of prefixes/resources for
various purposes.

### [`mismatch.json`](metaregistry.json)

This file contains the mismatch dictionary, so the alignment algorithm doesn't
accidentally create resources that are chimera of two different ones. Its keys
correspond to bioregistry prefixes and its values are dictionaries mapping from
metaprefixes to wrong external prefixes to avoid.
