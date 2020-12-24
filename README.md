<p align="center">
  <img src="docs/source/logo.png" height="150">
</p>

<h1 align="center">
    Bioregistry
</h1>

<p align="center">
    <a href="https://github.com/cthoyt/bioregistry/actions?query=workflow%3ATests">
        <img alt="Tests" src="https://github.com/cthoyt/bioregistry/workflows/Tests/badge.svg" />
    </a>
    <a href="https://pypi.org/project/bioregistry">
        <img alt="PyPI" src="https://img.shields.io/pypi/v/bioregistry" />
    </a>
    <a href="https://pypi.org/project/bioregistry">
        <img alt="PyPI - Python Version" src="https://img.shields.io/pypi/pyversions/bioregistry" />
    </a>
    <a href="https://github.com/cthoyt/bioregistry/blob/main/LICENSE">
        <img alt="PyPI - License" src="https://img.shields.io/pypi/l/bioregistry" />
    </a>
    <a href="https://zenodo.org/badge/latestdoi/319481281">
        <img src="https://zenodo.org/badge/319481281.svg" alt="DOI">
    </a>
</p>

An integrative registry of biological databases, ontologies, and nomenclatures.

## ⬇️ Download

The bioregistry database can be downloaded directly
from [here](https://github.com/cthoyt/bioregistry/blob/main/src/bioregistry/data/bioregistry.json)

## 🚀 Installation

```bash
$ pip install git+https://github.com/cthoyt/bioregistry.git
```

## Usage

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

## Update

```bash
$ bioregistry update
```
