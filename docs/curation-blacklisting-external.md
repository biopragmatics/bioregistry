---
layout: page
title: Blacklist External Prefixes
permalink: /curation/blacklist-external
---

When curating unaligned external prefixes, many are either out of scope or not
possible to find minimum metadata and therefore should be explicitly excluded
from the Bioregistry.

> **Warning ** This is a first draft of a tutorial on explicitly curating
> non-alignments. It's subject to change and additional polishing.

1. Identify a prefix of interest from BioPortal (or another) curation sheet
   (e.g.,
   [here](https://github.com/biopragmatics/bioregistry/blob/main/src/bioregistry/data/external/bioportal/curation.tsv))
2. Decide if it's out of scope:
   - Not enough information inside external registry's record to follow-up on
     what it is (i.e., `000467` in CHEMINF)
   - Is there evidence of this resource being used somewhere? Don't add
     resources that are one-off (e.g., many ontologies in BioPortal) as this
     pollutes the prefix pool and makes the burden of finding things harder
   - Double mapping to a Bioregistry prefix (there isn't currently a way to
     curate these)
   - Not about biomedical, chemical, clinical, or life sciences or meta-sciences
3. If out of scope, add to the SKIP list, either in the corresponding alignment
   python module or associated processing configuration (TODO this needs to be
   better standardized)

The PR [#41](https://github.com/semanticchemistry/semanticchemistry/issues/41)
demonstrates curating CHEMINF mappings including adding three explicit
blacklists.
