<p align="center">
  <img src="docs/source/logo.png" height="150">
</p>

<h1 align="center">
    Bioregistry
</h1>

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
