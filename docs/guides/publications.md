---
layout: page
title: Curating Publications and References
permalink: /curation/publications
---

The example below shows a subset of the record for
[3D Metabolites (3dmet)](https://bioregistry.io/3dmet) that highlights the
`publications` list. Note that each entry is a dictionary with several parts:

1. `title` (required) - the title of the paper
2. `year` (highly recommended) - the year of publication of the paper
3. `pubmed`, `doi`, and `pmc` (one or more required) - identifiers for the paper

```json
"3dmet": {
    "name": "3D Metabolites",
    "publications": [
      {
        "doi": "10.2142/biophysico.15.0_87",
        "pmc": "PMC5992871",
        "pubmed": "29892514",
        "title": "Chemical curation to improve data accuracy: recent development of the 3DMET database",
        "year": 2018
      },
      {
        "doi": "10.1021/ci300309k",
        "pubmed": "23293959",
        "title": "Three-dimensional structure database of natural metabolites (3DMET): a novel database of curated 3D structures",
        "year": 2013
      }
    ]
  },
```

Similarly, there are URL references that are not _publications_ that are worth
curating. These can be stored in the `references` list. For example, the
[Registry of Toxic Effects of Chemical Substances (rtecs)](https://bioregistry.io/rtecs)
entry appears in the Bioregistry because of its usage, but it is hard to find
information on the internet about it. Therefore, the references list is perfect
for storing references to PDFs and webpages that describe the resource.

```json
"rtecs": {
   "name": "Registry of Toxic Effects of Chemical Substances",
   "publications": [
   {
      "doi": "10.1016/s1074-9098%2899%2900058-1",
      "title": "An overview of the Registry of Toxic Effects of Chemical Substances (RTECS): Critical information on chemical hazards",
      "year": 1999
   }
   ],
   "references": [
      "https://www.cdc.gov/niosh/docs/97-119/pdfs/97-119.pdf",
      "https://www.cdc.gov/niosh/npg/npgdrtec.html"
   ]
}
```

What else is good to keep track of in the references list:

1. Bioregistry issue or pull requests about the resource
2. Links to webpages describing the identifier resource
3. Links to discussions on Slack or other platforms (keeping in mind links might
   not last forever)
4. Any other context that's useful for a Bioregistry reader

## Publications for Databases

A single database can correspond to several Bioregistry prefixes, such as in the
case of KEGG, ChEMBL, and even smaller resources like HGNC, which has both a
gene vocabulary ([`hgnc`](https://bioregistry.io/hgnc]) and gene group
vocabulary ([`hgnc.genegroup`](https://bioregistry.io/hgnc.genegroup)).

Publications are often made on the database level, so, therefore, if you want to
curate a publication for the database, it usually makes sense to duplicate the
publication into each prefix.

However, it's also possible that a long-standing database might have more
generic publications describing the whole database, and specific publications
describing a certain aspect. If one of the specific publications only
corresponds to a single prefix, then use your best judgement to not duplicate it
unnecessarily.

## Why Should I Curate Publications and References?

1. They give additional context for Bioregistry readers who want to know more
   about the paper
2. They make it easier to attribute usage of identifiers from a given resource
   to its authors
3. They enable global landscape analysis of when and where identifier resources
   are being made. The following image is automatically regenerated with each
   Bioregistry update:

   ![](https://raw.githubusercontent.com/biopragmatics/bioregistry/refs/heads/main/docs/img/bibliography_years.svg)

4. They support the training of a machine learning for semi-automated curation
   of additional literature. See this
   [talk](https://docs.google.com/presentation/d/1h2IajyGkUxUPHubEi8_WE6xW6TOuOihn5zsmi4kYrrc/edit?usp=sharing)
   from the 2022 Workshop on Prefixes, CURIEs, and IRIs.
