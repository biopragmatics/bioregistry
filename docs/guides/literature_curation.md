---
layout: page
title: Semi-automated Curation of New Prefixes, Providers, and Publications
permalink: /curation/literature
---

The Bioregistry aims to establish a comprehensive resource for the curation of biological identifiers. By efficiently identifying relevant resources, curators help expand the Bioregistry’s utility for the wider scientific community. This guide offers a structured approach for curators to assess and classify new information, ensuring that updates to the Bioregistry are both precise and thorough.

The Bioregistry uses a machine learning model to automatically identify PubMed papers that are potential candidates for
curation. Each month, the model produces a ranked list of papers based on their relevance to the Bioregistry. These
papers are relevant for expanding the Bioregistry in at least three ways:

1. As a **new prefix** for a resource providing primary identifiers,
2. As a **provider** for resolving existing identifiers,
3. As a **new publication** related to an existing prefix in the Bioregistry.

This guide provides a working table of relevancy_type tags, which are used to classify the relevance of each paper.
Curators can use these tags to categorize papers during the review process. The tags are part of the
following [TSV file]( https://github.com/biopragmatics/bioregistry/blob/main/src/bioregistry/data/curated_papers.tsv).
These updates help retrain the model, improving its accuracy over time.

The ranked list of suggested papers can be found [here]( https://github.com/biopragmatics/bioregistry/issues/1165). When
reviewing a paper, curators should update the TSV file with the following information:

- `pmid`: The PubMed ID of the paper being reviewed.
- `relevant`: 1 for relevant, 0 for not relevant.
- `orcid`: The ORCID of the curator reviewing the paper.
- `date_curated`: The date the paper was reviewed.
- `relevancy_type`: The type of relevance as defined in the table below.
- `pr_added`: The pull request number associated with the curation.
- `notes`: Any additional notes or comments regarding the paper's relevance or findings.



## Relevancy Type Table

This table of `relevancy_type` tags is continuously evolving as new papers are evaluated.

| Key                      | Definition                                                                |
|--------------------------|---------------------------------------------------------------------------|
| new_prefix               | A resource for new primary identifiers                                    |
| new_provider             | A resolver for existing identifiers                                       |
| new_publication          | A new publication for an existing prefix                                  |
| not_identifiers_resource | A database, but not for identifier information                            |
| no_website               | Paper suggestive of a new database, but no link to website provided       |
| existing                 | An existing entry in the bioregistry                                      |
| unclear                  | Not clear how to curate in the bioregistry, follow up discussion required |
| irrelevant_other         | Completely unrelated information                                          |

## Curation and Data Synchronization

When curators add rows to the curation TSV file, these entries should correspond to specific changes made in the
Bioregistry data files. Each pull request should encompass both the updates to the TSV file and the relevant
modifications to the data files in the Bioregistry repository.


## Common Mistakes

New curators may encounter some common challenges when reviewing papers and curating data. Below are a few mistakes to be aware of, along with tips on how to avoid them:

1. Confusing Databases with Semantic Spaces

One common mistake is focusing on describing the database rather than the semantic space it organizes. A database provides structured data, such as identifiers, while a semantic space organizes entities and their relationships within a conceptual framework.

When curating a resource, the Bioregistry record should describe the semantic space, that is, the entities and relationships the resource represents rather than the database itself. Explore the resource to identify multiple potential semantic spaces and curate separate prefixes for each entity type if necessary. The goal is to capture how the resource organizes and relates concepts, not just the data it holds.

3. Mislabeling Existing Resources as New

One common mistake is labeling an existing resource as a new prefix or provider. Before assigning a new_prefix or new_provider tag, first check if the resource is already listed in the Bioregistry. If the resource exists, consider whether the paper might be introducing a new publication associated with that resource, rather than a completely new entry. This prevents duplicate entries for existing resources.

4. Misunderstanding the Scope of Irrelevant Information

Not every paper mentioning biological resources is relevant to the Bioregistry. Papers that discuss databases not focused on identifier information, for example, should be marked as not_identifiers_resource. Similarly, entirely unrelated papers should be tagged as irrelevant_other. Being clear on the scope of the Bioregistry’s focus can help avoid curating irrelevant materials.



## Example curation

