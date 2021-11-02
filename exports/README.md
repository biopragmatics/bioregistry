# Bioregistry Exports

This folder contains the exports derived from the Bioregistry source files
for the registry, metaregistry, and collections. They are re-generated
on a nightly basis using GitHub Actions as a continuous integration server.

| Directory                       | Format                                                                                |
|---------------------------------|---------------------------------------------------------------------------------------|
|  [`registry`](registry)         | Exports of a consensus registry in JSON, YAML, and TSV                                |
|  [`metaregistry`](metaregistry) | Conversions of the metaregistry to YAML and TSV                                       |
|  [`collections`](collections)   | Conversions of the collections to YAML and TSV                                        |
|  [`rdf`](rdf)                   | Build of an RDF triple-store representing the registry, metaregistry, and collections |
|  [`contexts`](contexts)         | Fit-for-purpose exports of JSON-LD contexts constructed from the Bioregistry          |
