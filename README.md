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
from [here](https://github.com/cthoyt/bioregistry/blob/main/src/bioregistry/data/bioregistry.json).

The manually curated portions of these data are available under the CC0 1.0 Universal License.

## 🙏 Contributing

There haven't been any external contributors yet, but if you want to get involved, you can make edits directly to
the [bioregistry.json](https://github.com/cthoyt/bioregistry/blob/main/src/bioregistry/data/bioregistry.json)
file.

Things that would be helpful:

1. For all entries, add a `["wikidata"]["database"]` entry. Many ontologies and databases don't have a property in
   Wikidata because the process of adding a new property is incredibly cautious. However, anyone can add a database as
   normal Wikidata item with a Q prefix. One example is UniPathway, whose Wikidata database item
   is [Q85719315](https://www.wikidata.org/wiki/Q85719315). If there's no database item on Wikidata, you can even make
   one! Note: don't mix this up with a paper describing the
   resource, [Q35631060](https://www.wikidata.org/wiki/Q35631060). If you see there's a paper, you can add it under
   the `["wikidata"]["database"]` key.
2. Adding `["homepage"]` entry for any entry that doesn't have an external reference

## 🚀 Installation

```bash
$ pip install git+https://github.com/cthoyt/bioregistry.git
```

## 💪 Usage

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

## ♻️ Update

The database is automatically updated daily thanks to scheduled workflows in GitHub Actions. The workflow's
configuration can be found [here](https://github.com/cthoyt/bioregistry/blob/main/.github/workflows/update.yml)
and the last run can be
seen [here](https://github.com/cthoyt/bioregistry/actions?query=workflow%3A%22Update+Data%22). Further,
a [changelog](https://github.com/cthoyt/bioregistry/commits?author=actions-user) can be recapitulated from the commits
of the GitHub Actions bot.

If you want to manually update the database after installing in development mode, run the following:

```bash
$ bioregistry update
```
