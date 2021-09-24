<p align="center">
  <img src="https://github.com/biopragmatics/bioregistry/raw/main/docs/source/logo.png" height="150">
</p>

<h1 align="center">
    Bioregistry
</h1>

<p align="center">
    <a href="https://github.com/biopragmatics/bioregistry/actions?query=workflow%3ATests">
        <img alt="Tests" src="https://github.com/biopragmatics/bioregistry/workflows/Tests/badge.svg" />
    </a>
    <a href="https://pypi.org/project/bioregistry">
        <img alt="PyPI" src="https://img.shields.io/pypi/v/bioregistry" />
    </a>
    <a href="https://pypi.org/project/bioregistry">
        <img alt="PyPI - Python Version" src="https://img.shields.io/pypi/pyversions/bioregistry" />
    </a>
    <a href="https://github.com/biopragmatics/bioregistry/blob/main/LICENSE">
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
    <a href="https://biopragmatics.github.io/bioregistry/conduct/">
        <img alt="Contributor Covenant" src="https://img.shields.io/badge/Contributor%20Covenant-2.1-4baaaa.svg" />
    </a>
</p>

<p align="center">
   A community-driven integrative meta-registry of biological databases, ontologies, and other resources.
   <br />More information <a href="https://bioregistry.io/summary">here</a>.
</p>

The Bioregistry can be accessed, searched, and queried through its associated website at
https://bioregistry.io.

### 📥 Download

The underlying data of the Bioregistry can be downloaded directly
from [here](https://github.com/biopragmatics/bioregistry/blob/main/src/bioregistry/data/bioregistry.json).
Several exports to YAML, TSV, and RDF can be downloaded via https://bioregistry.io/download.

The manually curated portions of these data are available under the
[CC0 1.0 Universal License](https://creativecommons.org/publicdomain/zero/1.0/).

## 🙏 Contributing

If you'd like to request a new prefix, please fill out this [issue template](https://github.com/biopragmatics/bioregistry/issues/new?assignees=cthoyt&labels=New%2CPrefix&template=new-prefix.yml&title=Add+prefix+%5BX%5D).
It will automatically generate a pull request! Here's a list of all of the
open [requests for new prefixes](https://github.com/biopragmatics/bioregistry/issues?q=is%3Aissue+label%3APrefix+is%3Aopen).

There are a few other issue templates for certain updates (e.g., update regex, merge two prefixes, etc.) that you
can check [here](https://github.com/biopragmatics/bioregistry/issues/new/choose). For anything updates that don't
have a corresponding template, feel free to leave a freeform issue for us!

If you want to make a direct contribution, feel free to make edits directly to
the [bioregistry.json](https://github.com/biopragmatics/bioregistry/blob/main/src/bioregistry/data/bioregistry.json)
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
[here](https://biopragmatics.github.io/bioregistry/curation/). This page also has a more in-depth tutorial on how to contribute.

For more information on contributions, see [CONTRIBUTING.md](CONTRIBUTING.md).

## 🧹 Maintenance

### 🫀 Health Report

[![Health Report](https://github.com/biopragmatics/bioregistry/actions/workflows/health.yml/badge.svg)](https://github.com/biopragmatics/bioregistry/actions/workflows/health.yml)

The Bioregistry runs some automated tests weekly to check that various metadata haven't gone stale. For example,
it checks that the homepages are still available and that each provider URL is still able to resolve. The
tests fail if even a single metadata is out of place, so don't be frightened that this badge is almost always
red.

### ♻️ Update

The database is automatically updated daily thanks to scheduled workflows in GitHub Actions. The workflow's
configuration can be found [here](https://github.com/biopragmatics/bioregistry/blob/main/.github/workflows/update.yml)
and the last run can be seen [here](https://github.com/biopragmatics/bioregistry/actions?query=workflow%3A%22Update+Data%22).
Further, a [changelog](https://github.com/biopragmatics/bioregistry/commits?author=actions-user) can be recapitulated from the
commits of the GitHub Actions bot.

If you want to manually update the database after installing in development mode, run the following:

```shell
$ bioregistry update
```

## 🚀 Installation

The Bioregistry can be installed from [PyPI](https://pypi.org/project/bioregistry/) with:

```shell
$ pip install bioregistry
```

It can be installed in development mode for local curation with:

```shell
$ git clone https://github.com/biopragmatics/bioregistry.git
$ cd bioregistry
$ pip install --editable .
```

## 💪 Usage

### Normalizing Prefixes

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

### Parsing CURIEs

The Bioregistry supports parsing a CURIE into a pair of normalized prefix
and identifier using the `parse_curie()` function:

```python
from bioregistry import parse_curie

# Obvious for canonical CURIEs
assert ('chebi', '1234') == parse_curie('chebi:1234')

# Normalize common mistaken prefixes
assert ('pubchem.compound', '1234') == parse_curie('pubchem:1234')

# Normalize mixed case prefixes
assert ('fbbt', '1234') == parse_curie('FBbt:1234')

# Remove the redundant prefix and normalize
assert ('go', '1234') == parse_curie('GO:GO:1234')
```

### Normalizing CURIEs

The Bioregistry supports converting a CURIE to a canonical CURIE by normalizing
the prefix and removing redundant namespaces embedded in LUIs with the
`normalize_curie()` function.

```python
from bioregistry import normalize_curie

# Idempotent to canonical CURIEs
assert 'chebi:1234' == normalize_curie('chebi:1234')

# Normalize common mistaken prefixes
assert 'pubchem.compound:1234' == normalize_curie('pubchem:1234')

# Normalize mixed case prefixes
assert 'fbbt:1234' == normalize_curie('FBbt:1234')

# Remove the redundant prefix and normalize
assert 'go:1234' == normalize_curie('GO:GO:1234')
```

### Parsing IRIs

The Bioregistry can be used to parse CURIEs from IRIs due to its vast registry of provider URL
strings and additional programmatic logic implemented with Python. It can parse OBO Library PURLs,
IRIs from the OLS and identifiers.org, IRIs from the Bioregistry website, and any other IRIs
from well-formed providers registered in the Bioregistry. The `parse_iri()` function
gets a pre-parsed CURIE, while the `curie_from_iri()` function makes a canonical CURIE
from the pre-parsed CURIE.

```python
from bioregistry import curie_from_iri, parse_iri

# First-party IRI
assert ('chebi', '24867') == parse_iri('https://www.ebi.ac.uk/chebi/searchId.do?chebiId=CHEBI:24867')
assert 'chebi:24867' == curie_from_iri('https://www.ebi.ac.uk/chebi/searchId.do?chebiId=CHEBI:24867')

# OBO Library PURL
assert ('chebi', '24867') == parse_iri('http://purl.obolibrary.org/obo/CHEBI_24867')
assert 'chebi:24867' == curie_from_iri('http://purl.obolibrary.org/obo/CHEBI_24867')

# OLS IRI
assert ('chebi', '24867') == parse_iri('https://www.ebi.ac.uk/ols/ontologies/chebi/terms?iri=http://purl.obolibrary.org/obo/CHEBI_24867')
assert 'chebi:24867' == curie_from_iri('https://www.ebi.ac.uk/ols/ontologies/chebi/terms?iri=http://purl.obolibrary.org/obo/CHEBI_24867')

# Identifiers.org IRIs (with varying usage of HTTP(s) and colon/slash separator
assert ('chebi', '24867') == parse_iri('https://identifiers.org/CHEBI:24867')
assert ('chebi', '24867') == parse_iri('http://identifiers.org/CHEBI:24867')
assert ('chebi', '24867') == parse_iri('https://identifiers.org/CHEBI/24867')
assert ('chebi', '24867') == parse_iri('http://identifiers.org/CHEBI/24867')

# Bioregistry IRI
assert ('chebi', '24867') == parse_iri('https://bioregistry.io/chebi:24867')
```

### Generating IRIs

Given a pre-parse CURIE (e.g., a 2-tuple of a prefix and identifier), you
can get the Bioregistry's preferred IRI using `get_iri()`. By default, it uses
the following priorities:

1. First-party IRI
2. Identifiers.org / MIRIAM
3. Ontology Lookup Service
4. OBO PURL
5. Name-to-Thing
6. BioPortal

```python
import bioregistry

assert bioregistry.get_iri("chebi", "24867") == 'https://www.ebi.ac.uk/chebi/searchId.do?chebiId=CHEBI:24867' 
```

For convenience, you can also pass a regular CURIE to the first argument, and
it will get auto-parsed and auto-normalized:

```python
import bioregistry

assert bioregistry.get_iri("chebi:24867") == 'https://www.ebi.ac.uk/chebi/searchId.do?chebiId=CHEBI:24867' 
```

It's possible to change the default priority list by passing an alternate
sequence of metaprefixes to the `priority` keyword. For example, if you live
in the OBO world, you should make OBO PURLs the highest priority, then
when they aren't available, default to something else:

```python
import bioregistry

priority = ['obofoundry', 'bioregistry', 'default']
assert bioregistry.get_iri("chebi:24867", priority=priority) == 'http://purl.obolibrary.org/obo/CHEBI_24867' 
assert bioregistry.get_iri("hgnc:1234", priority=priority) == 'https://bioregistry.io/hgnc:1234' 
```

Alternatively, there are  direct functions for generating IRIs for different
registries:

```python
import bioregistry

# Bioregistry IRI
assert bioregistry.get_bioregistry_iri('chebi', '24867') == 'https://bioregistry.io/chebi:24867'

# Default Provider
assert bioregistry.get_default_iri('chebi', '24867') == 'https://www.ebi.ac.uk/chebi/searchId.do?chebiId=CHEBI:24867'

# OBO Library
assert bioregistry.get_obofoundry_iri('chebi', '24867') == 'http://purl.obolibrary.org/obo/CHEBI_24867'

# OLS IRI
assert bioregistry.get_ols_iri('chebi', '24867') == \
        'https://www.ebi.ac.uk/ols/ontologies/chebi/terms?iri=http://purl.obolibrary.org/obo/CHEBI_24867'

# Bioportal IRI
assert bioregistry.get_bioportal_iri('chebi', '24867') == \
        'https://bioportal.bioontology.org/ontologies/CHEBI/?p=classes&conceptid=http://purl.obolibrary.org/obo/CHEBI_24867'

# Identifiers.org IRI
assert bioregistry.get_identifiers_org_iri('chebi', '24867') == 'https://identifiers.org/CHEBI:24867'

# Name-to-Thing IRI
assert bioregistry.get_n2t_iri('chebi', '24867') == 'https://n2t.net/chebi:24867'
```

Each of these functions could also return `None` if there isn't a provider available or if the prefix
can't be mapped to the various resources.

### Getting Metadata

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

Entries in the Bioregistry can be looked up with the `get_resource()` function.

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

## 👋 Attribution

### ⚖️ License

The code in this repository is licensed under the
[MIT License](https://github.com/biopragmatics/bioregistry/blob/main/LICENSE).

### 📖 Citation

Hopefully there will be a paper describing this resource on *bioRxiv* sometime in 2021! Until then, you can use the
Zenodo [BibTeX](https://zenodo.org/record/4404608/export/hx) or [CSL](https://zenodo.org/record/4404608/export/csl).

### 🎁 Support

The Bioregistry was developed by the [INDRA Lab](https://indralab.github.io), a part of the
[Laboratory of Systems Pharmacology](https://hits.harvard.edu/the-program/laboratory-of-systems-pharmacology/about/)
and the [Harvard Program in Therapeutic Science (HiTS)](https://hits.harvard.edu)
at [Harvard Medical School](https://hms.harvard.edu/).

### 💰 Funding

The development of the Bioregistry is funded by the DARPA Young Faculty Award W911NF2010255 (PI: Benjamin M. Gyori).
