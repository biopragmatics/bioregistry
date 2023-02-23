---
layout: page
title: Who's Using the Bioregistry?
permalink: /usages/
---
{% for entry in site.data.usages %}

### {{ entry.name }}

<table class="table">
{% if entry.description %}
<tr>
<td><strong>Description</strong></td>
<td>{{ entry.description }}</td>
</tr>
{% endif %}
<tr>
<td><strong>Type</strong></td>
<td>{{ entry.type | capitalize }}</td>
</tr>
<tr>
<td><strong>Homepage</strong></td>
<td><a href="{{ entry.homepage }}">{{ entry.homepage }}</a></td>
</tr>
{% if entry.repository and entry.repository != entry.homepage %}
<tr>
<td><strong>Repository</strong></td>
<td><a href="{{ entry.repository }}">{{ entry.repository }}</a></td>
</tr>
{% endif %}
<tr>
<td><strong>Usages</strong></td>
<td>
<ul>
{% for usage in entry['uses'] %}
<li>
{{ usage['description'] }}
{% for link in usage['links'] %}
 <a href="{{ link }}">(ref)</a>
{% endfor %}
</li>
{% endfor %}
</ul>
</td>
</tr>
</table>

{% endfor %}
