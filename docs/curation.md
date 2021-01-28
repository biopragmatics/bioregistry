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



