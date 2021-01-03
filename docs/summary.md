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
ability to cover some of the most used resources like the HGNC.

<img src="https://raw.githubusercontent.com/cthoyt/bioregistry/main/docs/img/xrefs.png" alt="Reference Counts"/>

## Licensing

Licenses are only directly available from OBO Foundry and the OLS. Wikidata contains some licensing information, but
more code needs to be written to handle this.

<img src="https://raw.githubusercontent.com/cthoyt/bioregistry/main/docs/img/license_coverage.png" alt="License Coverage"/>

There are several conflicts, however, many of them involved inappropriate licenses for data such as the Apache 2.0
license and were collapsed into "Other". The remaining conflicts were between CC-BY and CC 0 references.

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
Wikidata property gateholders and the MIRIAM registry.
