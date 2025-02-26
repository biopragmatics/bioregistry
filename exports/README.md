# Bioregistry Exports

The source files of the Bioregistry can be accessed through
[this directory via GitHub](https://github.com/biopragmatics/bioregistry/tree/main/src/bioregistry/data).
Notably, the
[source file for the registry](https://github.com/biopragmatics/bioregistry/raw/main/src/bioregistry/data/bioregistry.json)
does not contain a consensus view, and therefore it's usually nicer to access
the Bioregistry's registry through the derived files below.

## Derived

This folder contains the exports derived from the Bioregistry source files for
the registry, metaregistry, and collections. They are re-generated on a weekly
basis using GitHub Actions as a continuous integration server.

| Directory                      | Format                                                                                           |
| ------------------------------ | ------------------------------------------------------------------------------------------------ |
| [`registry`](registry)         | Exports of a consensus registry in JSON, YAML, and TSV                                           |
| [`metaregistry`](metaregistry) | Conversions of the metaregistry to YAML and TSV                                                  |
| [`collections`](collections)   | Conversions of the collections to YAML and TSV                                                   |
| [`rdf`](rdf)                   | Build of an RDF triple-store representing the registry, metaregistry, and collections            |
| [`sssom`](sssom)               | An export of prefix mappings in the Simple Standard for Sharing Ontology Mappings (SSSOM) format |
| [`contexts`](contexts)         | Fit-for-purpose exports of JSON-LD contexts constructed from the Bioregistry                     |
| [`alignment`](alignment)       | Curation sheets for aligning the metaregistry                                                    |
| [`raw`](raw)                   | Raw data from select external registries                                                         |

## PURLs

The Bioregistry uses https://w3id.org to create persistent uniform resource
locators (PURLs) for various resources. These are configured on GitHub in the
`.htaccess` file in
https://github.com/perma-id/w3id.org/tree/master/biopragmatics.
