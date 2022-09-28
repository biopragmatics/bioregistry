---
layout: page
title: Health Report
permalink: /health/
---
{% assign run = site.data.health.runs.last %}

## Provider Health

Are local unique identifiers able to be resolved in the given URI format
strings?

### Summary

Of the {{ run.summary.total_measured }} prefixes that have both example local
unique identifiers and at least one URI format string,
{{ run.summary.failure_percent }}%
were able to resolve. This provides an upper bound, because some websites do not
give proper error messages for pages that are missing and instead redirect to
e.g. the homepage.

### Results

<table>
   <thead>
      <tr>
         <th>Date</th>
         <th>Prefix</th>
         <th>Example</th>
         <th>Status</th>
      </tr>
   </thead>
   <tbody>
   {% for record in run.results %}
      <tr>
         <td>{{ run.date }}</td>
         <td><a href="https://bioregistry.io/{{ record.prefix }}">{{ record.prefix }}</a></td>
         <td><a href="{{ record.url }}">{{ record.example }}</a></td>
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
