---
layout: page
title: Who's Using the Bioregistry?
permalink: /usages/
---
{% for entry in site.data.usages %}

## {{ entry.name }}

{{ entry }}

{% endfor %}
