---
layout: page
title: Curation
permalink: /curation/
---
This page has the curation todo list.

## Wikidata

The following entries in the Bioregistry have not been annotated with the `["wikidata"]["database"]` entry because it
either exists in Wikidata and it needs to be annotated, or it does not exist in Wikidata and needs to be created, then
annotated.

### Creating a Wikidata item

1. Create a [new item](https://www.wikidata.org/wiki/Special:NewItem)
2. Create the first relationship `instance of` ([P31](https://www.wikidata.org/wiki/Property:P31))
   and target `biological database` ([Q4117139](https://www.wikidata.org/wiki/Q4117139)).
3. Add second relationship `official website` ([P856](https://www.wikidata.org/wiki/Property:P856))
4. Fill in any other information you want! `country`, `main subject`, `maintained by`, etc.

### Editing the Bioregistry 

1. Follow [this link](https://github.com/cthoyt/bioregistry/edit/main/src/bioregistry/data/bioregistry.json) to edit
   directly on GitHub.
2. Here's an example of `3dmet`, which has the wikidata database annotated properly.
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
    <summary>Wikidata</summary>
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
        <td>{{ entry.name }}</td>
    </tr>
    {% endfor %}
</tbody>
</table>
</details>

## Patterns

Same drill for patterns - these entries need a `["pattern"]` entry.

<details>
    <summary>Pattern</summary>
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
        <td>{{ entry.name }}</td>
    </tr>
    {% endfor %}
</tbody>
</table>
</details>
