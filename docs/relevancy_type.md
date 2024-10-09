# Definitions of relevancy_type tags

This document provides a working table of relevancy_type tags and their definitions.

The relevancy_type tag is a column in the following [csv file]( https://github.com/biopragmatics/bioregistry/blob/main/src/bioregistry/curation/curated_papers.csv) used to retrain the ranking model for papers relevant for curation in the bioregistry.

This table is an evolving list that is subject to change as more papers are reviewed.


| **relevancy_type** | **definition** |
|--------------|--------------|
| new_prefix        | A resource for new primary identifiers       |
| new_provider      | A resolver for existing identifiers        |
| new_publication      | A new publication for an existing prefix       |
| not_identifiers_resource      | A database, but not for identifier information      |
| no_website       | Paper suggestive of a new database, but no link to website provided      |
| existing       | An existing entry in the bioregistry        |
| unclear      |  Not clear how to curate in the bioregistry, follow up discussion required     |
| irrelevant_other       | Completely unrelated information       |