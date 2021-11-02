# Bioregistry Exports

The source files of the Bioregistry can be accessed through
[this directory via GitHub](https://github.com/biopragmatics/bioregistry/tree/main/src/bioregistry/data).
Notably, the [source file for the registry](https://github.com/biopragmatics/bioregistry/raw/main/src/bioregistry/data/bioregistry.json)
does not contain a consensus view, and therefore it's usually nicer to access
the Bioregistry's registry through the derived files below.

## Derived

This folder contains the exports derived from the Bioregistry source files for
the registry, metaregistry, and collections. They are re-generated on a nightly
basis using GitHub Actions as a continuous integration server.

| Directory                       | Format                                                                                |
|---------------------------------|---------------------------------------------------------------------------------------|
|  [`registry`](registry)         | Exports of a consensus registry in JSON, YAML, and TSV                                |
|  [`metaregistry`](metaregistry) | Conversions of the metaregistry to YAML and TSV                                       |
|  [`collections`](collections)   | Conversions of the collections to YAML and TSV                                        |
|  [`rdf`](rdf)                   | Build of an RDF triple-store representing the registry, metaregistry, and collections |
|  [`contexts`](contexts)         | Fit-for-purpose exports of JSON-LD contexts constructed from the Bioregistry          |
