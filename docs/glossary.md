---
layout: page
title: Glossary
permalink: /glossary/
---

This section introduces several terms and their technical definitions when used
throughout this manuscript.

## Resource

A resource assigns unique identifiers to a collection of entities. This
definition is effectively interchangeable with _namespace_ and _semantic space_
in the context of the Bioregistry and other registries.

There are many types of resources such as ontologies (e.g.,
[Gene Ontology (GO)](https://bioregistry.io/go) ,
[Chemical Entities of Biological Interest (ChEBI)](https://bioregistry.io/chebi)
, [Experimental Factor Ontology (EFO)](https://bioregistry.io/efo)), controlled
vocabularies (e.g., [Entrez Gene](https://bioregistry.io/ncbigene) ,
[InterPro](https://bioregistry.io/interpro) ,
[FamPlex](https://bioregistry.io/famplex) ,
[HUGO Genome Nomenclature Consortium (HGNC)](https://bioregistry.io/hgnc), and
databases (e.g., [Protein Data Bank (PDB)](https://bioregistry.io/pdb) ,
[Gene Expression Omnibus (GEO)](https://bioregistry.io/geo)).

Some resources only cover single entity types (e.g., HGNC), some cover a small
number (e.g., Gene Ontology), and some are expansive (e.g.,
[MeSH](https://bioregistry.io/mesh), [UMLS](https://bioregistry.io/umls),
[NCI Thesaurus (NCIT)](https://bioregistry.io/efo)).

Some resources are complete by definition (e.g.,
[Enzyme Classification](https://bioregistry.io/ec)), some resources are complete
but subject to change (e.g., HGNC), and some are always incomplete (e.g., PDB).

Resources do not always correspond one-to-one with projects, such as how the
ChEMBL database contains both the
[ChEMBL Compound](https://bioregistry.io/chembl.compound) and
[ChEMBL Target](https://bioregistry.io/chembl.target) resources or how the Uber
Anatomy Ontology (UBERON) contains both [UBERON](https://bioregistry.io/uberon))
and UBPROP resources for terms and properties, respectively.

There are a variety of patterns used for identifiers, including integers
(`^\d+$`; e.g., PubMed), zero padded integers (`^\d{7}$`; e.g., GO, ChEBI, other
OBO Ontologies), universally unique identifiers (UUIDs; e.g., NCI Pathway
Interaction Database, NDEx), and many other variations.

## Record

A record is an entry in the Bioregistry or other external registry that has
information about a resource, such as its prefix, title, homepage, description,
etc.

## Provider

A provider returns information about entities from a given resource. A provider
is characterized by a URI format string into which an identifier from its
resource can be substituted for a special token (e.g., `$1`). For example, the
following formatter can be used to get a web page about a given HGNC entity
based on its identifier by replacing the `$1` with a given HGNC gene identifier
like `5173` for HRAS:
`http://www.genenames.org/cgi-bin/gene_symbol_report?hgnc_id=$1`.

Well-behaved URI format strings only have one instance of the special token that
occurs at the end. Poorly-behaved URI format strings may have additional
characters following the special token as in
`http://rebase.neb.com/rebase/enz/$1.html` for
[REBASE](https://bioregistry.io/rebase) or as in
http://eawag-bbd.ethz.ch/$1/$1_map.html for the
[UM-BBD Pathway database](https://bioregistry.io/umbbd.pathway). Providers can
return information HTML as in the previous example, images (e.g.,
https://www.ebi.ac.uk/chebi/displayImage.do?defaultImage=true&chebiId=132964 for
the ChEBI entry on fluazifop-P-butyl), XML (e.g.,
https://www.uniprot.org/uniprot/P10636.xml for UniProt entry on human
Microtubule-associated protein tau), or any other information that can be
transferred via HTTP, FTP, or related data transfer protocols. Alternatively,
content negotiation could be used to return multiple kinds of data from the same
provider URL. Most resources have an associated first-party provider that
returns information via a web page. Some resources, like ChEBI, have several
first-party providers for different content types (e.g., HTML, image). Some
resources, like Entrez Gene, have additional external providers, including
databases that use its identifiers like the Comparative Toxicogenomics Database
(CTD). Some resources, such as many OBO ontologies, do not have an associated
first party provider and rely solely on third party browsers like AberOWL,
OntoBee, and the Ontology Lookup Service.

## Registry

A registry is a special kind of resource that assigns unique identifiers to a
collection of resources. For historical reasons, these identifiers are
colloquially called prefixes. A registry collects additional metadata about each
resource, though there is a wide variety of metadata standards across existing
registries (see https://bioregistry.io/related). These metadata may include the
name, homepage, a regular expression pattern for validating identifiers, one or
more example identifiers, a default provider, and potentially additional
providers. Like with resources, a high-quality registry should have an
associated first-party provider that comprises a web site for exploring its
entries and their associated metadata. Some registries are directly imported and
reused in other places (e.g., GO Registry reused in psi-mi-CV
[https://github.com/HUPO-PSI/psi-ms-CV/blob/master/db-xrefs.yaml], NCBI GenBank
Registry reused in https://www.ddbj.nig.ac.jp/ddbj/db_xref-e.html).

## Metaregistry

A metaregistry is a special kind of registry that assigns unique identifiers to
a collection of registries; it could even contain an entry about itself. It
collects additional metadata about each registry, such as a description of its
metadata standards and capabilities (see https://bioregistry.io/related). Most
importantly, a metaregistry contains mappings between equivalent entries in its
constituent registries. Before the publication of this article, to the best of
our knowledge, there were no dedicated metaregistries. Some registries such as
FAIRSharing and the MIRIAM/Identifiers.org registry contain limited numbers of
entries referring to other registries (e.g., BioPortal), but they neither
delineate these records as representing registries, provide additional metadata,
nor provide mappings.

## Resolver

A resolver uses a registry to generate a URL for a given prefix/identifier pair
based on the registry's default provider for the resource with the given prefix,
then redirects the requester to the constructed URL. Resolvers are different
from providers in that they are general for many resources and do not host
content themselves. Four well-known resolvers are purl.org, the OBO PURL
service, and Identifiers.org. Name-To-Thing also includes other resolvers and is
therefore sometimes called a meta-resolver.

## Lookup Service

A lookup service is like a provider but generalized to provide for many
resources. They typically have a URL format string into which a compact
identifier can be placed like OntoBee, but many require more complicated
programmatic logic to construct. Some well-known lookup services are the OLS,
AberOWL, OntoBee, and BioPortal.

## Bioregistra

Noun: a developer, contributor, user, or supporter of the Bioregistry who loves
cute names for things. Plural: _Bioregistras_
