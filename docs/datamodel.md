---
layout: page
title: Data Model
permalink: /datamodel/
---

The following section describes the contents of entries in the Bioregistry. The
associated schema is encoded in Python classes using the
[Pydantic package](https://github.com/samuelcolvin/pydantic) which also
generates a generally reusable JSON schema. Each element of the schema has
associated unit tests that are run on any change to the Bioregistry to ensure
that not only the schema is conformant, but also enables higher-level tests for
style and content to be implemented.

<details>
   <summary>Expand for a UML diagram of the datamodel</summary>
   <img src="https://raw.githubusercontent.com/biopragmatics/bioregistry/main/docs/img/datamodel_umls.svg" alt="Bioregistry data model in a UML diagram"/>
</details>

## Metadata and Properties

### Prefixes

Each entry in the Bioregistry is annotated with a required canonical prefix
(i.e., lower case, containing no strange punctuation or characters), an optional
preferred prefix (i.e., containing stylization), and an optional list of
alternate prefixes (i.e., synonyms).

### Status

Each includes flags if the resource for the prefix is deprecated (e.g. AERO),
proprietary (e.g., NameRXN), or doesn't contain any terms (e.g., ChIRO). These
flags are helpful in subjectively deciding which resources could be considered
as reliable.

### Name, Description, and Homepage

All entries in the Bioregistry must have a name and description. This is
important not only for active resources, but also for deprecated resources so
the integrative registry can be used as a research tool and reference such as
when encountering the variety of historically obscured cross references in OBO
Foundry ontologies. All active resources must additionally have a homepage,
while inactive resources may not have a homepage due to their respective sites
being taken down. Entries are highly encouraged to include reference URLs and
contributor free text comments, especially for deprecated resources to give
context to readers.

### License

License information is only readily available via the OBO Foundry and Ontology
Lookup Service. Most use permissive licenses from the Creative Commons (either
CC-BY or CC-0). Some licenses include license versions and some do not. There
are several instances of conflict, often due to specification of the version of
the Creative Commons license. Licenses only appearing a small number of times,
such as CC-BY-SA, CC-BY-NC, and CC-BY-NC-SA were collapsed into "Other".
Licenses that were not appropriate for data (e.g., variants of the Apache
License, GNU GPL) and custom licenses (e.g., in the case of the Human Phenotype
Ontology) were also collapsed into "Other".

### Version

The OLS is the only registry that consumes the data it references and provides
detailed accessible artifacts, and is therefore the only registry that reports
version information. Other lookup services like AberOWL and OntoBee consume
ontologies but do not generate metadata reports. The OBO Foundry also references
versioned data, but does not consume it and therefore can not report version
information. Wikidata also contains version information for some databases, but
is not currently viable for generally tracking version information. The other
registries (e.g., MIRIAM, N2T) do not report version information as their
resolution services are independent of the data versions. Alternatively, the
Bioversions project sets out to be a registry-independent solution for
identifying current versions of different databases, ontologies, and resources.

### Local Unique Identifiers

All non-deprecated entries in the Bioregistry must include one or more example
local unique identifiers. While each optionally (highly recommended) includes a
regular expression pattern describing local unique identifiers, there are cases
when they are difficult to generate due to the high complexity and heterogeneity
of identifiers (e.g., Ensembl identifiers are highly complex), the lack of
enough examples as is often the case with deprecated identifiers, or the
triviality of assigning a wildcard pattern to a small enumerated namespace like
FOAF, RDF, or RDFS.

While the Bioregistry imports identifier regular expression patterns from
several registries (i.e., MIRIAM/Identifiers.org, N2T, Prefix Commons, GO, and
Wikidata), there exist many philosophical and practical discrepancies. A major
one arises in the definition and management of redundant prefixes embedded in
identifiers that is common to ontologies. For example, the colloquial local
unique identifier for apoptosis in the Gene Ontology is GO:0006915, so the
corresponding prefixed CURIE for this entity is GO:GO:0006915. Each registry
handles cases like this slightly differently, whether it is to include the
redundant prefix capitalized in the pattern, to include an extra flag in the
metadata associated with the prefix, or whether to completely handle this
programmatically.

In order to promote backwards compatibility with some MIRIAM prefixes, entries
can contain an annotation "namespace embedded in LUI" to allow for overriding of
MIRIAM metadata as well as the "banana" which explicitly states how the
namespace embedded in LUI appears, for situations where it is not the same as
the prefix itself (e.g., HOG).

Because there is such low consistency, the Bioregistry introduces a new field
called the "banana" where the potentially redundant prefix can be explicitly
enumerated, which allows for a general solution that can apply to FBbt, VariO,
and other mixed-case embedded prefixes. The Bioregistry Python package includes
functions for reformatting CURIEs based on the desired context (e.g., for
general use, for compatibility with Identifiers.org). Further discussion on this
topic can be found at https://github.com/biopragmatics/bioregistry/issues/191.

### URI Format String

Each entry optionally (highly recommended) includes one or more URI format
strings that can be used to generate URIs for a local unique identifier.

All active entries should have a provider, if possible. Deprecated resources
likely do not have providers. Two persisting issues are due to providers being
decommissioned but not removed from registries and the propagation of resolver
services as providers which exacerbates the first. For example, because many
ontologies use OBO-like PURLs, they are often annotated in registries as
providers even though they do not resolve to anything. It is a future goal to
provide more "health" checks over each registry and the Bioregistry as a whole.

### Availability

Each entry includes three optional fields for when the resource is available as
an ontology in the OWL (https://www.w3.org/TR/owl2-syntax), OBO
(https://owlcollab.github.io/oboformat/doc/obo-syntax.html), or OBO Graph JSON
(https://github.com/geneontology/obographs) formats. These entries are typically
imported from the OBO Foundry and OLS and are manually annotated to support
large-scale ontology acquisition and processing such as with ROBOT, Pronto, or
PyOBO.

### Attribution

Each includes two required attribution fields for the contributor and reviewer
that each require a minimum of an ORCiD identifier and name with optional email
address and GitHub handle. Each also includes an optional attribution field for
an external contact person for the resource that could have either the ORCiD
identifier, email, GitHub handle.

## Ontological Relationships Between Prefixes

In addition to metadata and properties, the Bioregistry includes rich
ontological relationships between prefixes in the Bioregistry as well as
external prefixes.

### Exact Matches

The most novel aspect of the Bioregistry is its ability to store equivalence
mappings (e.g., skos:exactMatch) between Bioregistry records and external
records (external records' semantics are mediated by the metaregistry). Each
entry in the Bioregistry can contain several mappings to different databases.
Typically, each prefix can only have one exact match in each database.
Exceptions have arisen due to duplicate records, in which case the mapping is
curated to the canonical external record. These records support interoperability
by enabling conversion between the standard flavor of a prefix defined by the
Bioregistry and context-specific variants.

### Depends On

Each entry contains a list of external entries that its associated resource
depends on. This is particularly useful in ontologies, since they may either
import terms from an external ontology or use external prefixes in their xrefs,
provenance, or relationships. These are mostly imported from the OBO Foundry but
also have an aspect of novel manual curation. While not explicitly stored in the
source data, the Bioregistry python package infers the inverse relationship (
i.e. appears in) for easy access given a prefix.

### Provides

While prefixes in the Bioregistry are supposed to correspond to nomenclature
authorities, this is not always true because it imports from external sources
that don't enforce this constraint. For example, the Comparative Toxicogenomics
Database uses NCBI Gene for naming genes and MeSH for naming diseases and
chemicals. Identifiers.org has minted 3 prefixes (ctd.gene, ctd.disease, and
ctd.chemical) that mostly reflect the entries of the authorities for which they
are providers. Another example is ValidatorDB, which provides information based
on Protein Databank records. An even more exotic example are the Gene Ontology
Annotations provided by the EBI because it provides for several types of
identifiers including those from UniProt, RNA Central, and the ComplexPortal.

Therefore, prefixes in the Bioregistry can be annotated with the prefix for
which they provide (e.g., ctd.gene provides mesh). Along with the part of and
has canonical relationships (described below), this relationship can promote
better standardization and help deconvolute multiple prefixes that use the same
URI format string, which is problematic when generating high quality prefix maps
for use in CURIE-IRI interconversion.

### Has Canonical

While there should not be redundancies in the Bioregistry, there are several
scenarios in which two or more prefixes equally correspond to the same
nomenclature authority. Because these can not be merged without making the data
model for the Bioregistry much more complicated and inaccessible, the has
canonical annotation allows for the subjective choice of which is considered
highest priority. A few scenarios in which this annotation is used are:

1. A prefix has been replaced by another one (e.g., hgnc.genefamily was replaced
   by hgnc.genegroup)
2. A prefix is redundant of another (e.g., glycomedb is redundant of glytoucan,
   pdb-ccd is redundant of pdb.ligand)
3. Multiple prefixes are used by different groups for the same shared semantic
   space, but none of them own it (e.g., insdc.run, ena.embl)

Records in the has canonical relationship do not necessarily have the same URI
format string, but if they do, this relationship further promotes choosing a
deterministic prefix when parsing an IRI in combination with the provides and
part of relationships.

### Part Of

There are several flavors of hierarchical relationships between prefixes in the
Bioregistry annotated with the part of relationship. For example,
chembl.compound and chembl.target are each a part of chembl and kegg.pathway and
kegg.ligand are each a part of kegg. Connecting these prefixes provides
significantly more context to readers of the Bioregistry. Other scenarios
include:

1. no shared prefix, has parent prefix (e.g., fbbt, fbcv, fbrf, ... and flybase)
2. has shared prefix, has dot delimiter, has a parent prefix (e.g., kegg with
   kegg.pathway, kegg.ligand),
3. has shared prefix, has dot delimiter, no parent prefix (e.g.,
   insdc.cds/insdc.gca/insdc.sra),
4. has shared prefix, no dot delimiter, has a parent prefix (N/A)
5. has shared prefix, no dot delimiter, no parent prefix (e.g., dlxb/dlxb,
   NCBIGene/NCBIProtein/NCBITaxon)
6. prefix matching resource name and extra prefixes (e.g., biogrid and
   biogrid.interaction)

In several cases such as KEGG and ChEMBL, the parent prefix and child prefixes
share a URI format string. Practically, the parent prefix would be sufficient,
but it is often pertinent to use a subspace to denote entity types within the
nomenclature. In the case of KEGG, each different entity type has a different
identifier pattern. In the case of ChEMBL, all different entity types have the
same identifier pattern. Ultimately, the part of relationship is the last part
combined with the provides and has canonical relationships along with a small
amount of additional logic to construct a high-quality prefix map.

The Rat Genome Database (RGD) constitutes an edge case with its three prefixes:
rgd, rgd.qtl, and rgd.strain. The rgd prefix is more of a bucket than a parent -
it includes all of the entity types (e.g., genes, articles) in the RGD that are
neither quantitative trait loci (QTLs) nor strains. Because of cases like this,
we have begun discussions on imposing a prefix subspacing policy at
https://github.com/biopragmatics/bioregistry/issues/133.
