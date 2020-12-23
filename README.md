<p align="center">
  <img src="docs/source/logo.png" height="150">
</p>

<h1 align="center">
    Bioregistry
</h1>

<p align="center">
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

The Bioregistry can be read in a Python project using:

```python
import bioregistry

registry = bioregistry.read_bioregistry()
```

## Update

```bash
$ bioregistry update
```
