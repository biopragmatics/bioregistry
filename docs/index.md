---
layout: home
---
<p align="center">
  <img src="https://raw.githubusercontent.com/bioregistry/bioregistry/main/docs/source/logo.png" height="150">
</p>

An integrative registry of biological databases, ontologies, and nomenclatures.

<table>
<thead>
<tr>
    <th>Prefix</th>
    <th>Name</th>
    <th>MIRIAM</th>
    <th>OLS</th>
    <th>OBO</th>
    <th>Wikidata</th>
</tr>
</thead>
<tbody>
{% for entry in site.data.bioregistry %}
    <tr>
        <td>{{ entry.prefix }}</td>
        <td>
            {% if entry.name %}
                {{ entry.name }}
            {% elsif entry.miriam.name %}
                {{ entry.miriam.name }}
            {% elsif entry.ols.name %}
                {{ entry.ols.name }}
            {% elsif entry.obofoundry.name %}
                {{ entry.obofoundry.name }}
            {% elsif entry.wikidata.name %}
                {{ entry.wikidata.name }}
            {% endif %}
        </td>
        <td>
            {% if entry.miriam %}
                <a href="https://registry.identifiers.org/registry/{{ entry.miriam.prefix }}">{{ entry.miriam.prefix }}</a>
            {% endif %}        
        </td>
        <td>
            {% if entry.ols %}
            <a href="https://www.ebi.ac.uk/ols/ontologies/{{ entry.ols.prefix }}">{{ entry.ols.prefix }}</a>
            {% endif %}
        </td>
        <td>
            {% if entry.obofoundry %}
            <a href="http://www.obofoundry.org/ontology/{{ entry.obofoundry.prefix }}.html">{{ entry.obofoundry.prefix }}</a>
            {% endif %}
        </td>
        <td>
            {% if entry.wikidata.property %}
            <a href="https://www.wikidata.org/wiki/Property:{{ entry.wikidata.property }}">{{ entry.wikidata.property }}</a>
            {% endif %}
        </td>
    </tr>
{% endfor %}
</tbody>
</table>
