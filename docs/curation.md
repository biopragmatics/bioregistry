---
layout: page
title: Help Wanted
permalink: /curation/
---

Welcome to the _Help Wanted_ section of the Bioregistry 👋, a place where both
first-time contributors or veteran Bioregistras can find small, meaningful ways
to contribute novel curations.

It's one of the core values of the Bioregistry project to provide attribution
and appreciation to curation contributors, here's how that works:

1. We associate your ORCID identifier with records that you submitted or helped
   improve. These are displayed proudly on our site's
   [contributions page](https://bioregistry.io/contributors/).
2. We associate your GitHub handle with the commits to the repository (even if
   one of the Bioregistry team members or an automated workflow on GitHub makes
   it on your behalf) to get GitHub cred.
3. We will consider _all_ curation contributors as co-authors on Bioregistry
   papers.

**Table of Contents**:

Each of the following sections has its own instructions on how to get started
making your own curations. If there's something unclear, please let us know via
the
[GitHub issue tracker](https://github.com/biopragmatics/bioregistry/issues/new),
and we can improve this page.

1. [Improving the Metaregistry](#improving-the-metaregistry)
2. [Aligning Wikidata database records](#wikidata)
3. [Curating regular expression patterns](#pattern)
4. [Curating URI format strings](#formatter)
5. [Curating example local unique identifiers](#example)

## Improving the Metaregistry

The Bioregistry processes and semi-automatically aligns metadata from external
registries such as Identifiers.org, the OBO Foundry, FAIRsharing, and others.
These alignments constitute the Bioregistry's _metaregistry_. Some resources
(e.g., Identifiers.org) have similar scope, minimum metadata standards, and
curation standards to the Bioregistry and are imported in full. Others are
aligned only when prefixes can be matched based on an algorithm.

This means that there are potentially many records in external registries that
are relevant for the Bioregistry, but either were not able to be mapped to an
existing prefix, or do not have a mapping but would be valuable to import.

The following table links to curation sheets for each external registry that
show relevant metadata to help curate each record as one of the following:

1. Record corresponds to a prefix in the Bioregistry. Tutorial TBD.
2. Record is relevant but does not have a corresponding prefix in the
   Bioregistry. See the tutorial on
   [importing external prefixes](import-external).
3. Record is irrelevant for the bioregistry. See the tutorial on
   [curating explicit prefix blacklists](blacklist-external).

<table>
<thead>
   <tr>
      <th>Prefix</th>
      <th>Name</th>
   </tr>
</thead>
<tbody>
{% for entry in site.data.curation["prefix_xrefs"] %}
   <tr>
      <td>{{ entry.metaprefix }}</td>
      <td><a href="https://github.com/biopragmatics/bioregistry/blob/main/exports/alignment{{ entry.metaprefix }}.tsv">{{ entry.name }}</a></td>
   </tr>
{% endfor %}
</tbody>
</table>

<a id="wikidata"></a>

## Aligning Wikidata Database Records

The following entries in the Bioregistry have not been annotated with the
`["wikidata"]["database"]` entry because it either exists in Wikidata and it
needs to be annotated, or it does not exist in Wikidata and needs to be created,
then annotated.

### Creating a Wikidata item

1. Make sure an item doesn't exist already by doing a cursory search of
   Wikidata.
2. Create a [new item](https://www.wikidata.org/wiki/Special:NewItem).
3. Create the first relationship `instance of`
   ([P31](https://www.wikidata.org/wiki/Property:P31)) and target
   `biological database` ([Q4117139](https://www.wikidata.org/wiki/Q4117139)).
4. Add second relationship `official website`
   ([P856](https://www.wikidata.org/wiki/Property:P856))
5. Fill in any other information you want! `country`, `main subject`,
   `maintained by`, etc.

### Editing the Bioregistry

1. Fork the repository, clone it, create a new branch, and edit the
   [src/bioregistry/data/bioregistry.json](https://github.com/bioregistry/bioregistry/edit/main/src/bioregistry/data/bioregistry.json)
   file locally. Check the
   [contribution guidelines](https://github.com/biopragmatics/bioregistry/blob/main/docs/CONTRIBUTING.md)
   for help on working with Git and GitHub
2. Here's an example of `3dmet`, which has the Wikidata database annotated
   properly.

   ```json
   {
      "3dmet": {
         "miriam": {
            "deprecated": false,
            "description": "3DMET is a database collecting three-dimensional structures of natural metabolites.",
            "id": "00000066",
            "name": "3DMET",
            "namespaceEmbeddedInLui": false,
            "pattern": "^B\\d{5}$",
            "prefix": "3dmet"
         },
         "n2t": {
            "prefix": "3dmet"
         },
         "wikidata": {
            "database": "Q23948774",  // <-- this is it!!
            "property": "P2796"
         }
      },
      ...
   }
   ```

<details>
   <summary>Entries ({{ site.data.curation["wikidata"] | size }})</summary>
   <table>
   <thead>
      <tr>
         <th>Prefix</th>
         <th>Name</th>
      </tr>
   </thead>
   <tbody>
   {% for entry in site.data.curation["wikidata"] %}
      <tr>
         <td>{{ entry.prefix }}</td>
         <td><a href="{{ entry.homepage }}">{{ entry.name }}</a></td>
      </tr>
   {% endfor %}
   </tbody>
   </table>
</details>

<a id="pattern"></a>

## Adding a Regular Expression Pattern for Each Resource's Local Unique Identifiers

Same drill for patterns - these entries need a `["pattern"]` entry that includes
a regular expression describing the local unique identifiers for this namespace.

<details>
   <summary>Entries ({{ site.data.curation["pattern"] | size }})</summary>
   <table>
   <thead>
      <tr>
         <th>Prefix</th>
         <th>Name</th>
      </tr>
   </thead>
   <tbody>
   {% for entry in site.data.curation["pattern"] %}
      <tr>
         <td>{{ entry.prefix }}</td>
         <td><a href="{{ entry.homepage }}">{{ entry.name }}</a></td>
      </tr>
   {% endfor %}
   </tbody>
   </table>
</details>

<a id="formatter"></a>

## Curating URI Format Strings

Same drill for URL Formatters - these entries need a `["uri_format"]` entry.
This is a URL with a `$1` character where the local unique identifier gets put.

```json
{
  ...
  "jax": {
    "example": "004435",
    "name": "Jackson Laboratories Strain",
    "uri_format": "https://www.jax.org/strain/$1"
    // <-- this one here
  },
  ...
}
```

<details>
   <summary>Entries ({{ site.data.curation["formatter"] | size }})</summary>
   <table>
   <thead>
      <tr>
         <th>Prefix</th>
         <th>Name</th>
      </tr>
   </thead>
   <tbody>
   {% for entry in site.data.curation["formatter"] %}
      <tr>
         <td>{{ entry.prefix }}</td>
         <td><a href="{{ entry.homepage }}">{{ entry.name }}</a></td>
      </tr>
   {% endfor %}
   </tbody>
   </table>
</details>

<a id="example"></a>

## Example Local Unique Identifier

As a courtesy to newcomers, it's nice to show an example local unique
identifier. These entries need a `["example"]` entry.

```json
{
  ...
  "jax": {
    "example": "004435",
    // <-- this one here
    "name": "Jackson Laboratories Strain",
    "url": "https://www.jax.org/strain/$1"
  },
  ...
}
```

<details>
   <summary>Entries ({{ site.data.curation["example"] | size }})</summary>
   <table>
   <thead>
      <tr>
         <th>Prefix</th>
         <th>Name</th>
      </tr>
   </thead>
   <tbody>
   {% for entry in site.data.curation["example"] %}
      <tr>
         <td>{{ entry.prefix }}</td>
         <td><a href="{{ entry.homepage }}">{{ entry.name }}</a></td>
      </tr>
   {% endfor %}
   </tbody>
   </table>
</details>
