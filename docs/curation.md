---
layout: page
title: Help Wanted
permalink: /curation/
---
This page has the curation To-Do list.

## Curating Cross-Registry Mappings

The following registries have xrefs that need curating:

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
      <td><a href="https://github.com/biopragmatics/bioregistry/blob/main/src/bioregistry/data/external/{{ entry.metaprefix }}/curation.tsv">{{ entry.name }}</a></td>
   </tr>
{% endfor %}
</tbody>
</table>

See also the following tutorials:

1. [importing external prefixes](/curation/import-external)
2. [curating explicit prefix blacklists](/curation/blacklist-external)

## Adding a Wikidata Database Corresponding to Each Resource

<a id="wikidata"></a>
The following entries in the Bioregistry have not been annotated with
the `["wikidata"]["database"]` entry because it either exists in Wikidata and it
needs to be annotated, or it does not exist in Wikidata and needs to be created,
then annotated.

### Creating a Wikidata item

1. Make sure an item doesn't exist already by doing a cursory search of
   Wikidata.
2. Create a [new item](https://www.wikidata.org/wiki/Special:NewItem).
3. Create the first relationship `instance of` ([P31](https://www.wikidata.org/wiki/Property:P31))
   and target `biological database` ([Q4117139](https://www.wikidata.org/wiki/Q4117139)).
4. Add second relationship `official website` ([P856](https://www.wikidata.org/wiki/Property:P856))
5. Fill in any other information you want! `country`, `main subject`,
   `maintained by`, etc.

### Editing the Bioregistry

1. Follow [this link](https://github.com/bioregistry/bioregistry/edit/main/src/bioregistry/data/bioregistry.json)
   to edit directly on GitHub.
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

## Adding a Regular Expression Pattern for Each Resource's Local Unique Identifiers

<a id="pattern"></a>
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

## URI Format

<a id="formatter"></a>
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

## Example Local Unique Identifier

<a id="example"></a>
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
