---
layout: page
title: Health Report
permalink: /health/
---
{% assign run = site.data.health.runs[0] %}

## Provider Health

Are local unique identifiers able to be resolved in the given URI format
strings?

### Summary

Of the {{ run.summary.total_measured }} prefixes in the Bioregistry that have
both example local unique identifiers and at least one URI format string,
{{ run.summary.total_failed }} ({{ run.summary.failure_percent }}%) were able to
resolve with a HTTP 200. This provides an upper bound, because some websites do
not give proper error messages for pages that are missing and instead redirect
to e.g. the homepage.

{% if run.delta %}

### Changes

{% if run.delta.new.size > 0 or run.delta.fallen.size > 0 %}
New failures (passing in the previous check but not in the current check):

<ul>
{% for prefix in run.delta.new %}
<li>[{{ prefix }}](https://bioregistry.io/{{ prefix }}) (first check)</li>
{% endfor %}
{% for prefix in run.delta.fallen %}
<li><a href="https://bioregistry.io/{{ prefix }}">{{ prefix }}</a></li>
{% endfor %}
</ul>
{% endif %}

{% if run.delta.revived and run.delta.revived.size > 0 %}
Revived (i.e., failed in the previous check but passed in the current check):
<ul>
{% for prefix in run.delta.revived %}
<li><a href="https://bioregistry.io/{{ prefix }}">{{ prefix }}</a></li>
{% endfor %}
</ul>
{% endif %}

{% if run.delta.forgotten and run.delta.forgotten.size > 0 %}
Forgotten (i.e., tested in the previous check but not this check):
<ul>
{% for prefix in run.delta.forgotten %}
<li><a href="https://bioregistry.io/{{ prefix }}">{{ prefix }}</a></li>
{% endfor %}
</ul>
{% endif %}
{% endif %}

### Results ({{ run.date }})

<table>
   <thead>
      <tr>
         <th>Prefix</th>
         <th>Example</th>
         <th>Status</th>
      </tr>
   </thead>
   <tbody>
   {% for record in run.results %}
      <tr>
         <td><a href="https://bioregistry.io/{{ record.prefix }}">{{ record.prefix }}</a></td>
         <td><a href="{{ record.url | uri_escape }}">{{ record.example | truncate: 30 }}</a></td>
         <td>
            {% if record.exception %}
                {{ record.exception }}
            {% elsif record.status_code == 200 %}
                HTTP {{ record.status_code }}
            {% else %}
                HTTP {{ record.status_code }}
            {% endif %}
        </td>
      </tr>
   {% endfor %}
   </tbody>
</table>
