<p align="center">
  <img src="https://github.com/bioregistry/bioregistry/raw/main/docs/source/logo.png" height="150">
</p>

<h1 align="center">
    Bioregistry
</h1>

<p align="center">
    <a href="https://github.com/bioregistry/bioregistry/actions?query=workflow%3ATests">
        <img alt="Tests" src="https://github.com/bioregistry/bioregistry/workflows/Tests/badge.svg" />
    </a>
    <a href="https://pypi.org/project/bioregistry">
        <img alt="PyPI" src="https://img.shields.io/pypi/v/bioregistry" />
    </a>
    <a href="https://pypi.org/project/bioregistry">
        <img alt="PyPI - Python Version" src="https://img.shields.io/pypi/pyversions/bioregistry" />
    </a>
    <a href="https://github.com/bioregistry/bioregistry/blob/main/LICENSE">
        <img alt="PyPI - License" src="https://img.shields.io/pypi/l/bioregistry" />
    </a>
    <a href='https://bioregistry.readthedocs.io/en/latest/?badge=latest'>
        <img src='https://readthedocs.org/projects/bioregistry/badge/?version=latest' alt='Documentation Status' />
    </a>
    <a href="https://zenodo.org/badge/latestdoi/319481281">
        <img src="https://zenodo.org/badge/319481281.svg" alt="DOI">
    </a>
    <a href="https://github.com/psf/black">
        <img src="https://img.shields.io/badge/code%20style-black-000000.svg" alt="Code style: black">
    </a>
</p>

<p align="center">
   A community-driven integrative meta-registry of biological databases, ontologies, and other resources.
   <br />More information <a href="https://bioregistry.io/summary/">here</a>.
</p>

## ⬇️ Download

The bioregistry database can be downloaded directly
from [here](https://github.com/bioregistry/bioregistry/blob/main/src/bioregistry/data/bioregistry.json).

The manually curated portions of these data are available under the CC0 1.0 Universal License.

## 🙏 Contributing

There haven't been any external contributors yet, but if you want to get involved, you can make edits directly to
the [bioregistry.json](https://github.com/bioregistry/bioregistry/blob/main/src/bioregistry/data/bioregistry.json)
file through the GitHub interface.

Things that would be helpful:

1. For all entries, add a `["wikidata"]["database"]` entry. Many ontologies and databases don't have a property in
   Wikidata because the process of adding a new property is incredibly cautious. However, anyone can add a database as
   normal Wikidata item with a Q prefix. One example is UniPathway, whose Wikidata database item
   is [Q85719315](https://www.wikidata.org/wiki/Q85719315). If there's no database item on Wikidata, you can even make
   one! Note: don't mix this up with a paper describing the
   resource, [Q35631060](https://www.wikidata.org/wiki/Q35631060). If you see there's a paper, you can add it under
   the `["wikidata"]["paper"]` key.
2. Adding `["homepage"]` entry for any entry that doesn't have an external reference

A full list of curation to-do's is automatically generated as a web page
[here](https://bioregistry.github.io/bioregistry/curation/). This page also has a more in-depth tutorial on how to contribute.

## 🚀 Installation

The Bioregistry can be installed from [PyPI](https://pypi.org/project/bioregistry/) with:

```bash
$ pip install bioregistry
```

It can be installed in development mode for local curation with:

```bash
$ git clone https://github.com/bioregistry/bioregistry.git
$ cd bioregistry
$ pip install -e .
```

## 💪 Usage

The Bioregistry can be used to normalize prefixes across MIRIAM and all the (very plentiful) variants that pop up in
ontologies in OBO Foundry and the OLS with the `normalize_prefix()` function.

```python
import bioregistry

# This works for synonym prefixes, like:
assert 'ncbitaxon' == bioregistry.normalize_prefix('taxonomy')

# This works for common mistaken prefixes, like:
assert 'pubchem.compound' == bioregistry.normalize_prefix('pubchem')

# This works for prefixes that are often written many ways, like:
assert 'eccode' == bioregistry.normalize_prefix('ec-code')
assert 'eccode' == bioregistry.normalize_prefix('EC_CODE')

# If a prefix is not registered, it gives back `None`
assert bioregistry.normalize_prefix('not a real key') is None
```

The pattern for an entry in the Bioregistry can be looked up quickly with `get_pattern()` if
it exists. It prefers the custom curated, then MIRIAM, then Wikidata pattern.

```python
import bioregistry

assert '^GO:\\d{7}$' == bioregistry.get_pattern('go')
```

Entries in the Bioregistry can be checked for deprecation with the `is_deprecated()` function. MIRIAM and OBO Foundry
don't often agree - OBO Foundry takes precedence since it seems to be updated more often.

```python
import bioregistry

assert bioregistry.is_deprecated('nmr')
assert not bioregistry.is_deprecated('efo')
```

Entries in the Bioregistry can be looked up with the `get()` function.

```python
import bioregistry

entry = bioregistry.get_resource('taxonomy')
# there are lots of mysteries to discover in this dictionary!
```

The full Bioregistry can be read in a Python project using:

```python
import bioregistry

registry = bioregistry.read_registry()
```

## 🕸️ Resolver App

After installing with the `[web]` extras, run the resolver CLI with

```shell
$ bioregistry web
```

to run a web app that functions like Identifiers.org, but backed by the Bioregistry.
A public instance of this app is hosted by the [INDRA Lab](https://indralab.github.io) at 
https://bioregistry.io.

## ♻️ Update

The database is automatically updated daily thanks to scheduled workflows in GitHub Actions. The workflow's
configuration can be found [here](https://github.com/bioregistry/bioregistry/blob/main/.github/workflows/update.yml)
and the last run can be seen [here](https://github.com/bioregistry/bioregistry/actions?query=workflow%3A%22Update+Data%22).
Further, a [changelog](https://github.com/bioregistry/bioregistry/commits?author=actions-user) can be recapitulated from the
commits of the GitHub Actions bot.

If you want to manually update the database after installing in development mode, run the following:

```bash
$ bioregistry update
```

## ⚖️ License

The code in this repository is licensed under the
[MIT License](https://github.com/bioregistry/bioregistry/blob/main/LICENSE).

## 📖 Citation

Hopefully there will be a paper describing this resource on *bioRxiv* sometime in 2021! Until then, you can use the
Zenodo [BibTeX](https://zenodo.org/record/4404608/export/hx) or [CSL](https://zenodo.org/record/4404608/export/csl).

## 💰 Funding

The development of the Bioregistry is funded by the DARPA Young Faculty Award W911NF2010255 (PI: Benjamin M. Gyori).
