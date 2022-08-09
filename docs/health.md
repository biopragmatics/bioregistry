---
layout: page
title: Health Report
permalink: /health/
---
This page checks the health of the resources

### Provider Health

Are local unique identifiers able to be resolved in the given URI format
strings?

<table>
   <thead>
      <tr>
         <th>Prefix</th>
         <th>Name</th>
         <th>Example</th>
         <th>Error</th>
      </tr>
   </thead>
   <tbody>
   {% for entry in site.data.health %}
      <tr>
         <td><code>{{ entry.prefix }}</code></td>
         <td>{{ entry.name }}</td>
         <td><a href="{{ entry.url }}"><code>{{ entry.example }}</code></a></td>
         <td>
            {% if entry.contact_name %}
            <a href="mailto:{{ entry.contact_email }}">{{ entry.contact_name }}</a>
            {% endif %}
        </td> 
      </tr>
   {% endfor %}
   </tbody>
</table>
