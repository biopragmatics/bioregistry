---
layout: page
title: Download
permalink: /download/
---
The bioregistry database can be downloaded directly
from [here](https://github.com/cthoyt/bioregistry/blob/main/src/bioregistry/data/bioregistry.json).

## License

The manually curated portions of these data are available under the CC0 1.0 Universal License.

## Programmatic Access

The Bioregistry can be used to normalize prefixes across MIRIAM and all the (very plentiful) variants that pop up in
ontologies in OBO Foundry and the OLS with the `normalize_prefix()` function.

```python
import bioregistry

# This works for synonym prefixes, like:
assert 'ncbitaxon' == bioregistry.normalize_prefix('taxonomy')

# This works for common mistaken prefixes, like:
assert 'chembl.compound' == bioregistry.normalize_prefix('chembl')

# This works for prefixes that are often written many ways, like:
assert 'eccode' == bioregistry.normalize_prefix('ec-code')
assert 'eccode' == bioregistry.normalize_prefix('EC_CODE')

# If a prefix is not registered, it gives back `None`
assert bioregistry.normalize_prefix('not a real key') is None
```

Entries in the Bioregistry can be looked up with the `get()` function.

```python
import bioregistry

entry = bioregistry.normalize_prefix('taxonomy')
# there are lots of mysteries to discover in this dictionary!
```

The full Bioregistry can be read in a Python project using:

```python
import bioregistry

registry = bioregistry.read_bioregistry()
```

The source code can be found at [https://github.com/cthoyt/bioregistry](https://github.com/cthoyt/bioregistry).
