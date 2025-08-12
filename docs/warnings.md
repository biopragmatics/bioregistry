---
layout: page
title: Warnings
permalink: /warnings/
---

This lists any sorts of things that should be fixed upstream, but are instead
manually curated in the Bioregistry.

## License Conflicts

The following chart shows which manual annotations in the OBO Foundry are
inconsistent with those extracted by the OLS.

<table>
   <thead>
      <tr>
         <th>Prefix</th>
         <th>OBO License</th>
         <th>OLS License</th>
      </tr>
   </thead>
   <tbody>
   {% for entry in site.data.warnings["license_conflict"] %}
      <tr>
         <td><a href="https://bioregistry.io/{{ entry.prefix }}"><code>{{ entry.prefix }}</code></a></td>
         <td><code>{{ entry.obo }}</code></td>
         <td><code>{{ entry.ols }}</code></td>
      </tr>
   {% endfor %}
   </tbody>
</table>

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

### Embedding of Namespace in LUI

The following entries have an incorrect value in the `namespaceEmbeddedInLui`
field.

<table>
   <thead>
      <tr>
         <th>Prefix</th>
         <th>Name</th>
         <th>Pattern</th>
         <th>MIRIAM</th>
         <th>Correct</th>
      </tr>
   </thead>
   <tbody>
   {% for entry in site.data.warnings["embedding_rewrites"] %}
      <tr>
         <td><code>{{ entry.prefix }}</code></td>
         <td><a href="{{ entry.homepage }}">{{ entry.name }}</a></td>
         <td>{{ entry.pattern }}</td>
         <td>{{ entry.miriam }}</td>
         <td>{{ entry.correct }}</td>
      </tr>
   {% endfor %}
   </tbody>
</table>

### Prefix Mismatch when Namespace Embedded in LUI

When the namespace is embedded in the LUI, it's expected that the prefix should
be uppercased. This is often not the case.

<table>
   <thead>
      <tr>
         <th>Prefix</th>
         <th>Name</th>
         <th>Pattern</th>
         <th>Correct Prefix</th>
      </tr>
   </thead>
   <tbody>
   {% for entry in site.data.warnings["prefix_rewrites"] %}
      <tr>
         <td><code>{{ entry.prefix }}</code></td>
         <td><a href="{{ entry.homepage }}">{{ entry.name }}</a></td>
         <td><code>{{ entry.pattern }}</code></td>
         <td><code>{{ entry.correct }}</code></td>
      </tr>
   {% endfor %}
   </tbody>
</table>
