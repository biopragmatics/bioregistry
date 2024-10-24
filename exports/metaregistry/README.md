# Metaregistry Exports

This directory contains derived files from the metaregistry. The reference file
can be accessed
[here](https://github.com/biopragmatics/bioregistry/raw/main/src/bioregistry/data/metaregistry.json).

### [`metaregistry.yml`](metaregistry.yml)

This is exactly the same as the source `metaregistry.json` file, but converted
to the YAML format.

### [`metaregistry.tsv`](metaregistry.tsv)

This is a derived view over the metaregistry in a tab-separated values document.
It is _not necessarily_ a full view over the metaregistry, but only contains
fields which are the most important.

If there's something additional you'd like included in this export, please open
an issue.
