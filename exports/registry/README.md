# Registry Exports

This directory contains derived files from the registry.

While the reference file can be accessed
[here](https://github.com/biopragmatics/bioregistry/raw/main/src/bioregistry/data/metaregistry.json),
it does not constitute a consensus view. This is because the registry file is
set up to contain only novel manual curation, imports from external registries,
and manual overrides. The logic for accessing the data is inside the associated
Python code. However, the logic is applied to create the following derived
consensus files.

### [`registry.json`](registry.json)

This is a consensus view over the registry in the JSON format. It combines all
the novel curation in the registry, prioritized information from external
registries, and manual overrides into a streamlined, slimmed down version of the
registry.

This file _should_ contain all relevant fields. If you find something missing,
please make an issue.

This file can be accessed with the PURL:
https://w3id.org/biopragmatics/bioregistry/registry.json

### [`registry.yml`](registry.yml)

This is exactly the same as the consensus `registry.json` but dumped as a YAML
file.

This file can be accessed with the PURL:
https://w3id.org/biopragmatics/bioregistry/registry.yml

### [`registry.tsv`](registry.tsv)

This is a derived view over the registry in a tab-separated values document. It
is _not_ a full view over the registry, but only contains fields which are the
most important.

If there's something additional you'd like included in this export, please open
an issue.

This file can be accessed with the PURL:
https://w3id.org/biopragmatics/bioregistry/registry.tsv

### [`publications.tsv`](publications.tsv)

This is a derived view of all the publications referenced by various records in
the Bioregistry.
