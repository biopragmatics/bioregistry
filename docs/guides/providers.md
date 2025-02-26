---
layout: page
title: Curating Providers
permalink: /curation/providers
---

The example below shows a subset of the record for
[Chemical Entities of Biological Interest (ChEBI)](https://bioregistry.io/chebi)
that highlights three parts:

1. `uri_format` - this is the default string used to turn a local unique
   identifier into a URL for resolution. Many Bioregistry records reuse the
   `uri_format` annotation from an external registry like Identifiers.org, so
   you might notice in the edit file that this is missing. Even when a
   `uri_format` is available from external registries, it can still be
   explicitly overriden. URI format strings use a `$1` as the placeholder for
   the local unique identifier.
2. `rdf_uri_format` - the semantic web community prefers to have exactly one URI
   format string that is used in all semantic web artifacts. When this is not
   controversial, it can be explicitly annotated, such as for OBO Foundry
   ontologies.
3. `providers` - this is a place to put additional URI format strings, that are
   either useful for resolution or for parsing non-resolvable URIs that may
   appear in data. Each provider requires a minimum of 5 pieces of information:
   1. `code` - A short code that represents this provider. It is not globally
      unique, but it must be locally unique with respect to other providers in a
      given Bioregistry record
   2. `homepage`, `description`, `name` - helpful metadata for users and
      curators to understand why this provider exists and what it does
   3. `uri_format` - the URI format, same as above

```json
{
  "chebi": {
    "name": "Chemical Entities of Biological Interest",
    "uri_format": "https://www.ebi.ac.uk/chebi/searchId.do?chebiId=$1",
    "rdf_uri_format": "http://purl.obolibrary.org/obo/CHEBI_$1",
    "providers": [
      {
        "code": "chebi-img",
        "description": "Image server from chebi",
        "homepage": "https://www.ebi.ac.uk/chebi/",
        "name": "ChEBI",
        "uri_format": "https://www.ebi.ac.uk/chebi/displayImage.do?defaultImage=true&chebiId=$1"
      }
    ]
  }
}
```

## What Should I Curate as a Provider?

1. Additional endpoints that give different kinds of information, such as image
   resolution, JSON/XML/structured data artifacts, or other
2. URI patterns that appear in data, but aren't necessarily for resolution

## Providers for a Subset

Some providers only resolve a subset of the corresponding semantic space. For
example, the Immune Epitope Database providers for UniProt identifiers, but only
the subset that have been curated as antigens.

In general, it's okay to curate such providers, given that the description field
makes it clear what the limitations are.

## What Can I Do with Providers?

The Bioregistry resolver has the ability to redirect based on providers. For
example, https://bioregistry.io/chebi:138488 will redirect based on the default
URI format string associated with the `chebi` prefix, but the `provider`
parameter can be provided to redirect using a different provider based on its
code. This means that https://bioregistry.io/chebi:138488?provider=chebi-img
will redirect to a 2D depiction of the chemical structure of alsterpaullone.
