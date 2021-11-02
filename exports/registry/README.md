# Registry Exports

This directory contains derived files from the registry.

### [`registry.json`](registry.json)

This is a consensus view over the registry in the JSON format. It combines all
the novel curation in the registry, prioritized information from external
registries, and manual overrides into a streamlined, slimmed down version of the
registry.

This file *should* contain all relevant fields. If you find something missing,
please make an issue.

### [`registry.yml`](registry.yml)

This is exactly the same as `registry.json` but dumped as a YAML file.

### [`registry.tsv`](registry.tsv)

This is a derived view over the registry in a tab-separated values document. It
is *not* a full view over the registry, but only contains fields which are the
most important.

If there's something additional you'd like included in this export, please open
an issue.