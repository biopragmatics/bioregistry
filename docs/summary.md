---
layout: page
title: Summary
permalink: /summary/
---

## Bioregistry Coverage

This two-sided comparison shows how well the Bioregistry covers each external registry. In the case of Wikidata, it's
difficult to know exactly how many relevant properties there are.

<img src="https://raw.githubusercontent.com/cthoyt/bioregistry/main/docs/img/bioregistry_coverage.png" alt="Bioregistry Coverage"/>

## Overlap between External Registries

After normalization and integration in the Bioregistry, it's possible to investigate the overlap between pairs of other
registries. It can be seen that the MIRIAM and Name-to-Thing (N2T) registries are effectively the same because N2T
imports from MIRIAM. It can also be seen that OLS and OBO Foundry have a very high overlap, where the OLS includes
several ontologies that are not included in OBO Foundry. Notably, this discrepancy contains the highly regarded
Experimental Factor Ontology (EFO).

<img src="https://raw.githubusercontent.com/cthoyt/bioregistry/main/docs/img/external_overlap.png" alt="External Registry Overlaps"/>

## Highly Conserved Resources

The following chart shows how often entries in the Bioregistry have few or many references to external registries. A few
resources appear in all external registries, such as the NCBI Taxonomy database. However, the notable lack of inclusion
of controlled vocabularies that aren't *technically* ontologies into the OBO Foundry and OLS severely lacks their
ability to cover some of the most used resources like the HGNC. Entries with no references are uniquely curated in the
Bioregistry.

<img src="https://raw.githubusercontent.com/cthoyt/bioregistry/main/docs/img/xrefs.png" alt="Reference Counts"/>

## Licensing

Licenses are only directly available from OBO Foundry and the OLS. Wikidata contains some licensing information, but
more would need to be written to handle this.

<img src="https://raw.githubusercontent.com/cthoyt/bioregistry/main/docs/img/license_coverage.png" alt="License Coverage"/>

However, even internally, neither the OBO Foundry nor OLS use a consistent nomenclature for licenses, so they were
remapped using [this ruleset](https://github.com/cthoyt/bioregistry/blob/main/src/bioregistry/compare.py#L19). Further,
some licenses that were inappropriate for data (e.g., Apache 2.0 License, GNU GPL 3.0 License, BSD License) appeared
infrequently and were collapsed into "Other". Other uncommon and infrequent licenses were likewise collapsed into
"Other". After, there were still several conflicts between the reported license in OBO Foundry and OLS, in which case
both were added to the tally. In the majority of the conflicts, OBO Foundry reported CC-BY and OLS reported CC 0.

<img src="https://raw.githubusercontent.com/cthoyt/bioregistry/main/docs/img/licenses.png" alt="License Types"/>

## Other Attributes

<img src="https://raw.githubusercontent.com/cthoyt/bioregistry/main/docs/img/has_attribute.png" alt="Attributes Coverage"/>

### Versioning

The OLS is the only registry that actually consumes the data it references, and is therefore the only registry that
reports version information. The OBO Foundry also references versioned data, but does not consume it and therefore can
not report version information. Wikidata also contains version information for some databases, but is not currently
viable for generally tracking version information. The other registries (e.g., MIRIAM, N2T) do no report version
information as their resolution services are independent of the data versions. Alternatively,
the [Bioversions](https://github.com/cthoyt/bioversions) project sets out to be a registry-independent solution for
identifying current versions of different databases, ontologies, and resources.

### Pattern

MIRIAM and Wikidata are only registies that report patterns, though OBO Foundry has a very consistent pattern of most
OBO ontologies using the `^<prefix>:\d{7}$` pattern. However, this isn't a rule, so it can't be assumed without
inspection of some terms from the ontology itself. The Bioregistry also has a place to curate patterns for all the
entries that do not have a reference in MIRIAM.

### Wikidata Database

It's typically difficult to propose new Wikidata properties to go along with databases, but anyone can add entities
corresponding to databases. This is one part of the Bioregistry that will require lots of manual effort. Eventually, we
can develop a minimum information standard for entries in the Bioregistry that would be convincing enough for the
Wikidata property gatekeepers and the MIRIAM registry.
