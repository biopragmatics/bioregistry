---
layout: page
title: Semi-automated Curation of New Prefixes, Providers, and Publications
permalink: /curation/literature
---

The Bioregistry uses a machine learning model to automatically identify PubMed papers that are potential candidates for
curation. Each month, the model produces a ranked list of papers based on their relevance to the Bioregistry. These
papers are relevant for expanding the Bioregistry in at least three ways:

1. As a **new prefix** for a resource providing primary identifiers,
2. As a **provider** for resolving existing identifiers,
3. As a **new publication** related to an existing prefix in the Bioregistry.

This guide provides a working table of relevancy_type tags, which are used to classify the relevance of each paper.
Curators can use these tags to categorize papers during the review process. The tags are part of the
following [csv file]( https://github.com/biopragmatics/bioregistry/blob/main/src/bioregistry/curation/curated_papers.csv).
These updates help retrain the model, improving its accuracy over time.

The ranked list of suggested papers can be found [here]( https://github.com/biopragmatics/bioregistry/issues/1165). When
reviewing a paper, curators should update the CSV file with the following information:

- `pmid`: The PubMed ID of the paper being reviewed.
- `relevant`: 1 for relevant, 0 for not relevant.
- `relevancy_type`: The type of relevance as defined in the table below.
- `notes`: Any additional notes or comments regarding the paper's relevance or findings.
- `orcid`: The ORCID of the curator reviewing the paper.
- `date`: The date the paper was reviewed.

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

When curators add rows to the curation CSV file, these entries should correspond to specific changes made in the
Bioregistry data files. Each pull request should encompass both the updates to the CSV file and the relevant
modifications to the data files in the Bioregistry repository.
