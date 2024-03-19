---
layout: page
title: Health Report
permalink: /health/
---
{% assign run = site.data.health.runs[0] %}

Of the {{ run.summary.total_measured }} prefixes in the Bioregistry that have
both an example local unique identifiers and at least one URI format string,
{{ run.summary.total_success }} ({{ run.summary.success_percent }}%)
were able to resolve (with a HTTP 200 status code) and {{ run.summary.total_failed }}
({{ run.summary.failure_percent }}%) were not.

This comes with a few caveats:

1. Some websites do not send appropriate HTTP statuses, and may return HTTP 200
   even when redirecting to a default "Page Not Found" page. This means that this
   number might be artificially high.
2. There are several reasons why resolution might fail, some of which are false
   positives (see below).

**Why Does Resolution Fail?**

1. The website has been updated, and the URI format does not correspond to an
   existing endpoint anymore (solvable with additional curation).
2. The website has been fully taken down
3. The website has been replaced with another unrelated website, and the URI
   format does not correspond to an existing endpoint anymore (e.g., the old
   site for `atfdb.family` has been replaced by something unrelated).
4. The website suffered from a temporary issue and failed to resolve during
   check, but still works. Because this is possible, it's better to compare the
   last few checks for any newly failing prefixes.
5. The website never existed in the first place. Some URI format strings are
   generated as artifacts of ontology curation,
   e.g., with [Protégé](https://protege.stanford.edu), and were not meant to
   resolve. Ontologies typically use IRIs (a superset of URIs), which do not
   necessarily imply that their content are resolvable as a URL.
6. The URI corresponds to a redirect that is misconfigured in the redirection
   service (e.g., this happened for several CropOCT ontologies
   (ref: [#527](https://github.com/biopragmatics/bioregistry/issues/527)) and
   sporadically for the OBO PURL service).
7. The URI format string was curated incorrectly.

**Why Store URI Formats for Dead Resources?**

It's still valuable to store URI format strings, even if the websites don't work
anymore (or never did in the first place), because URIs based on these URI
format strings may appear in biomedical resources like ontologies or databases.
This makes the Bioregistry a more valuable tool for parsing these URIs and
ultimately for standardizing data.

{% if run.delta %}

### Changes

There are {{ run.delta.alive }} prefixes that remain passing and
{{ run.delta.dead }} that remained failing.

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
      {% if record.exception %}
         {% assign color = "#FFDDDB" %}
      {% elsif record.status_code == 200 %}
         {% assign color = "#B0EEB0" %}
      {% else %}
         {% assign color = "#FFFFE0" %}
      {% endif %}
      <tr style="background-color: {{ color }}">
         <td><a href="https://bioregistry.io/{{ record.prefix }}">{{ record.prefix }}</a></td>
         <td><a href="{{ record.url | uri_escape }}">{{ record.example | truncate: 30 }}</a></td>
         <td>
            {% if record.exception %}
                {{ record.exception }}
            {% else %}
                HTTP {{ record.status_code }}
            {% endif %}
        </td>
      </tr>
   {% endfor %}
   </tbody>
</table>
