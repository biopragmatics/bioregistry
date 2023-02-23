---
layout: page
title: Who's Using the Bioregistry?
permalink: /usages/
---
{% for entry in site.data.usages %}

### {{ entry.name }}

<table class="table">
<tr>
<td><strong>Type</strong></td>
<td>{{ entry.type | capitalize }}</td>
</tr>
<tr>
<td><strong>Homepage</strong></td>
<td><a href="{{ entry.link }}">{{ entry.link }}</a></td>
</tr>
</table>

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

{% endfor %}
