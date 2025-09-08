---
layout: page
title: Semi-automated Curation of New Prefixes, Providers, and Publications
permalink: /curation/literature
---

The Bioregistry aims to establish a comprehensive resource for the curation of
biological identifiers. By efficiently identifying relevant resources, curators
help expand the Bioregistry’s utility for the wider scientific community. This
guide offers a structured approach for curators to assess and classify new
information, ensuring that updates to the Bioregistry are both precise and
thorough.

The Bioregistry uses a machine learning model to automatically identify PubMed
papers that are potential candidates for curation. Each month, the model
produces a ranked list of papers based on their relevance to the Bioregistry.
These papers are relevant for expanding the Bioregistry in at least three ways:

1. As a **new prefix** for a resource providing primary identifiers,
2. As a **new provider** for resolving existing identifiers,
3. As a **new publication** related to an existing prefix in the Bioregistry.

This guide provides a working table of `relevancy_type` tags, which are used to
classify the relevance of each paper. Curators can use these tags to categorize
papers during the review process. The tags are part of the following
[TSV file](https://github.com/biopragmatics/bioregistry/blob/main/src/bioregistry/data/curated_papers.tsv).
These updates help retrain the model, improving its accuracy over time.

The ranked list of suggested papers can be found
[here](https://github.com/biopragmatics/bioregistry/issues/1165). When reviewing
a paper, curators should update the TSV file with the following information:

- `pmid`: The PubMed ID of the paper being reviewed.
- `relevant`: 1 for relevant, 0 for not relevant.
- `orcid`: The ORCID of the curator reviewing the paper.
- `date_curated`: The date the paper was reviewed.
- `relevancy_type`: The type of relevance as defined in the table below.
- `pr_added`: The pull request number associated with the curation.
- `notes`: Any additional notes or comments regarding the paper's relevance or
  findings.

## Relevancy Type Table

This table of `relevancy_type` tags is continuously evolving as new papers are
evaluated and is subject to change in the future.

| Key                      | Definition                                                                                                   |
| ------------------------ | ------------------------------------------------------------------------------------------------------------ |
| new_prefix               | A resource for new primary identifiers                                                                       |
| new_provider             | A resolver for existing identifiers                                                                          |
| new_publication          | A new publication for an existing prefix                                                                     |
| not_identifiers_resource | Papers linking to external non-identifier resources such as software repositories, visualization tools, etc. |
| non_resource_paper       | Self-contained papers that do not link to any external resources                                             |
| existing                 | An existing entry in the bioregistry                                                                         |
| unclear                  | Not clear how to curate in the bioregistry, follow up discussion required                                    |
| irrelevant_other         | Completely unrelated information                                                                             |
| not_notable              | Relevant for training purposes, but not curated in Bioregistry due to poor/unknown quality                   |

## Common Mistakes

New curators may encounter some common challenges when reviewing papers and
curating data. Below are a few mistakes to be aware of, along with tips on how
to avoid them:

**1. Confusing Databases with Semantic Spaces**

One common mistake is focusing on describing the database rather than the
semantic space it organizes. A database provides structured data, such as
identifiers, while a semantic space organizes entities and their relationships
within a conceptual framework.

When curating a resource, the Bioregistry record should describe the semantic
space, that is, the entities and relationships the resource represents rather
than the database itself. Explore the resource to identify multiple potential
semantic spaces and curate separate prefixes for each entity type if necessary.
The goal is to capture how the resource organizes and relates concepts, not just
the data it holds.

**2. Mislabeling Existing Resources as New**

Another common mistake is labeling an `existing` resource as a `new_prefix` or
`new_provider`. Before curating a `new_prefix` or `new_provider`, first check if
the resource is already listed in the Bioregistry. If the resource exists,
consider whether the paper might be introducing a `new_publication` associated
with that resource, rather than a completely new entry. This prevents duplicate
entries for existing resources.

**3. Misunderstanding the Scope of Irrelevant Information**

Not every paper mentioning biological resources is relevant to the Bioregistry.
Papers that discuss databases not focused on identifier information, for
example, should be marked as `not_identifiers_resource`. Similarly, entirely
unrelated papers should be tagged as `irrelevant_other`. Being clear on the
scope of the Bioregistry’s focus can help avoid curating irrelevant materials.

## Curation and Data Synchronization

When curators add rows to the curation TSV file, these entries should correspond
to specific changes made in the Bioregistry data files. Each pull request should
encompass both the updates to the TSV file and the relevant modifications to the
data files in the Bioregistry repository.

## Step-by-Step Example to Curating a New Prefix

The following step-by-step example is for the resource
[SCancerRNA](http://www.scancerrna.com/) based on the publication
[SCancerRNA: Expression at the Single-cell Level and Interaction Resource of Non-coding RNA Biomarkers for Cancers](https://pubmed.ncbi.nlm.nih.gov/39341795/).

**1. Assess the Database for Identifier Creation**

Begin by exploring the database to determine if it generates new identifiers for
life sciences entities. This is an investigative process, and there isn’t a
one-size-fits-all approach; however, most databases typically have a Browse or
Search section, which serves as a good starting point. Take your time to
navigate various categories to confirm that the resource creates relevant
identifiers. Once verified, proceed to fill out the TSV file with the
preliminary information you gathered.

| pmid     | relevant | orcid               | date_curated | relevancy_type | pr_added | notes                                                |
| -------- | -------- | ------------------- | ------------ | -------------- | -------- | ---------------------------------------------------- |
| 39341795 | 1        | 0009-0009-5240-7463 | 2024-10-19   | new_prefix     | 1215     | identifiers of non-coding RNA biomarkers for cancers |

**2. Collect Essential Information**

Gather easily accessible information for the resource, such as:

- Name and Email for a point of contact (github and ORCID if possible as well)
- Example identifier
- Homepage URL
- Name of the resource
- Publication information (such as PubMed ID, DOI, title, year)
- URI format to resolve identifiers

This data will be necessary for filling out the Bioregistry record.

**3. Write a Brief Description**

Create a concise description that explains what kind of entities the resource
makes identifiers for and its general purpose.

**4. Write a Regex Pattern**

Examine the format of the identifiers used by the resource and write a regex
pattern to validate this format. It’s better to create a pattern that is
somewhat flexible to accommodate potential future identifier additions.

**5. Update `bioregistry.json`**

```json
"scancerna": {
    "contact": {
      "email": "zty2009@hit.edu.cn",
      "name": "Tianyi Zhao",
      "orcid": "0000-0001-7352-2959"
    },
    "contributor": {
      "email": "m.naguthana@hotmail.com",
      "github": "nagutm",
      "name": "Mufaddal Naguthanawala",
      "orcid": "0009-0009-5240-7463"
    },
    "description": "SCancerRNA provides identifiers for non-coding RNA biomarkers, including long ncRNA, microRNA, PIWI-interacting RNA, small nucleolar RNA, and circular RNA, with data on their differential expression at the cellular level in cancer.",
    "example": "9530",
    "github_request_issue": 1215,
    "homepage": "http://www.scancerrna.com/",
    "name": "SCancerRNA",
    "pattern": "^\\d+$",
    "publications": [
      {
        "doi": "10.1093/gpbjnl/qzae023",
        "pubmed": "39341795",
        "title": "SCancerRNA: Expression at the Single-cell Level and Interaction Resource of Non-coding RNA Biomarkers for Cancers",
        "year": 2024
      }
    ],
    "uri_format": "http://www.scancerrna.com/toDetail?id=$1"
  },
```

**6. Submit a Pull Request**

Submit a pull request with the changes you made to both the TSV file and the
`bioregistry.json` file. Make sure the PR includes all necessary updates.

## Example Prefix Curation with Multiple Semantic Spaces

In this example, two prefixes have been curated from the Asteraceae Genome
Database (AGD), based on the publication
[Asteraceae Genome Database: A Comprehensive Platform for Asteraceae Genomics](https://pmc.ncbi.nlm.nih.gov/articles/PMC11366637/).

The dot notation is used to indicate that both `asteraceaegd.genome` and
`asteraceaegd.plant` are part of the same overarching resource (AGD), but each
prefix represents a distinct semantic space:

- `asteraceaegd.genome` focuses on the genomic information for Asteraceae
  species.
- `asteraceaegd.plant` focuses on the broader phenotypic and genetic data about
  Asteraceae plants.

By curating separate prefixes for each semantic space, the Bioregistry ensures
clear and precise representation of the different types of data provided by the
AGD. This approach allows users to distinguish between the different kinds of
identifiers and the types of biological information they refer to within the
same database.

```json
"asteraceaegd.genome": {
    "contact": {
      "email": "greatchen@cdutcm.edu.cn",
      "name": "Wei Chen"
    },
    "contributor": {
      "email": "m.naguthana@hotmail.com",
      "github": "nagutm",
      "name": "Mufaddal Naguthanawala",
      "orcid": "0009-0009-5240-7463"
    },
    "description": "The AGD is an integrated database resource dedicated to collecting the genomic-related data of the Asteraceae family. This collection refers to the genomic data of Asteraceae species.",
    "example": "0002",
    "github_request_issue": 1214,
    "homepage": "https://cbcb.cdutcm.edu.cn/AGD/",
    "name": "Asteraceae Genome Database",
    "pattern": "^\\d{4}$",
    "publications": [
      {
        "doi": "10.3389/fpls.2024.1445365",
        "pmc": "PMC11366637",
        "pubmed": "39224843",
        "title": "Asteraceae genome database: a comprehensive platform for Asteraceae genomics",
        "year": 2024
      }
    ],
    "uri_format": "https://cbcb.cdutcm.edu.cn/AGD/genome/details/?id=$1"
  },
"asteraceaegd.plant": {
    "contact": {
      "email": "greatchen@cdutcm.edu.cn",
      "name": "Wei Chen"
    },
    "contributor": {
      "email": "m.naguthana@hotmail.com",
      "github": "nagutm",
      "name": "Mufaddal Naguthanawala",
      "orcid": "0009-0009-5240-7463"
    },
    "description": "The AGD is an integrated database resource dedicated to collecting the genomic-related data of the Asteraceae family. This collections refers to the broader phenotypic and genetic resources of Asteraceae plants.",
    "example": "0016",
    "github_request_issue": 1214,
    "homepage": "https://cbcb.cdutcm.edu.cn/AGD/",
    "name": "Asteraceae Genome Database",
    "pattern": "^\\d{4}$",
    "publications": [
      {
        "doi": "10.3389/fpls.2024.1445365",
        "pmc": "PMC11366637",
        "pubmed": "39224843",
        "title": "Asteraceae genome database: a comprehensive platform for Asteraceae genomics",
        "year": 2024
      }
    ],
    "uri_format": "https://cbcb.cdutcm.edu.cn/AGD/plant/details/?id=$1"
  },
```
