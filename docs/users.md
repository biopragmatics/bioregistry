---
layout: page
title: Who's Using the Bioregistry?
permalink: /usages/
---

Are you using the Bioregistry and want your project/organization on this list?
Please let us know on the
[issue tracker](https://github.com/biopragmatics/bioregistry/issues/new).

To find new users, start with this
[GitHub search for the Bioregistry](https://github.com/search?q=%22import+bioregistry%22+OR+%22from+bioregistry+import%22+-user%3Acthoyt+-user%3Asorgerlab+-user%3Abiopragmatics+-is%3Afork+-user%3Apyobo+-user%3Apybel+-user%3Agyorilab&type=code).
Similarly, downstream users of the Bioregistry often use the
[`curies`](https://github.com/cthoyt/curies) package. See its usages with
[this search](https://github.com/search?q=%22import+curies%22+OR+%22from+curies+import%22+-user%3Acthoyt+-user%3Asorgerlab+-user%3Abiopragmatics+-is%3Afork+-user%3Apyobo+-user%3Apybel+-user%3Agyorilab+-repo%3ANCATS-Gamma%2Frobokop+-repo%3Anutanix%2Fcurie+language%3APython&type=code&p=4&l=Python).

{% for entry in site.data.usages %}

### {{ entry.name }}{% if entry.logo %}<img src="{{ entry.logo }}" style="margin-left: 5px; max-height: 35px;" />{% endif %}

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
{% if entry.wikidata %}
<tr>
<td><strong>Wikidata</strong></td>
<td><a href="https://scholia.toolforge.org/{{ entry.wikidata }}">{{ entry.wikidata }}</a></td>
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
