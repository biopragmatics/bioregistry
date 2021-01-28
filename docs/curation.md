---
layout: page
title: Curation
permalink: /curation/
---
This page has the curation todo list.

## Wikidata

The following entries in the Bioregistry do not have a corresponding entry in Wikidata
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



