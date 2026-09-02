---
layout: page
title: Warnings
permalink: /warnings/
---

This lists any sorts of things that should be fixed upstream, but are instead
manually curated in the Bioregistry.

## MIRIAM

The following issues are with the integrity of the data in the MIRIAM registry (
identifiers.org).

### Incorrect Pattern

The following entries have an incorrect value in the `pattern` field.

<table>
   <thead>
      <tr>
         <th>Prefix</th>
         <th>Name</th>
         <th>MIRIAM</th>
         <th>Correct</th>
      </tr>
   </thead>
   <tbody>
   {% for entry in site.data.warnings["wrong_patterns"] %}
      <tr>
         <td><code>{{ entry.prefix }}</code></td>
         <td><a href="{{ entry.homepage }}">{{ entry.name }}</a></td>
         <td><code>{{ entry.miriam }}</code></td>
         <td><code>{{ entry.correct }}</code></td>
      </tr>
   {% endfor %}
   </tbody>
</table>
