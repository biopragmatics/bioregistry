---
layout: page
title: Importing External Prefixes
permalink: /curation/import-external
---

While the Bioregistry automatically imports all prefixes from external
registries with similar scope and sufficient minimum metadata and quality
standards (e.g., Identifiers.org), it only partially aligns most external
registries (e.g., BioPortal). This is a tutorial on how to import a prefix from
one of the partially aligned registries on an _as-needed_ basis. More
specifically, it describes importing the _Food classification_
([`FOODEX2`](http://agroportal.lirmm.fr/ontologies/FOODEX2)) ontology from
AgroPortal. Pull request
[#573](https://github.com/biopragmatics/bioregistry/pull/573) contains the
relevant diff for the changes described in this tutorial.

1. Identify a prefix of interest from AgroPortal (or another) curation sheet
   (e.g.,
   [here](https://github.com/biopragmatics/bioregistry/blob/main/src/bioregistry/data/external/agroportal/curation.tsv))
2. Pick a prefix for the Bioregistry. This doesn't have to be the same as the
   external one, but usually it is. If the external prefix is too short or too
   vague, it might be a good chance to improve on this. Further, keep in mind
   that Bioregistry requires lowercase, so the best choice here is `foodex2`
3. Go into the `bioregistry.json` file and use the prefix as a key for a new
   dictionary object.
4. The only thing you need inside the object is `"mappings"` which itself is a
   dictionary object where the key is the metaprefix for the external registry
   (in this case `agroportal`) and the value is the external registry's prefix
   (in this case `FOODEX2`).

   ```json
   "foodex2": {
       "mappings": {
           "agroportal": "FOODEX2"
       }
   }
   ```

5. Make sure the Bioregistry is installed in editable mode
6. Run the alignment script for the registry. In this case, it's
   `python -m bioregistry.align.bioportal`
7. Run unit tests with `tox -e py`. This reveals that the alignment doesn't pull
   in enough metadata to meet the minimum requirements. In this case, OntoPortal
   instances (e.g., AgroPortal, BioPortal, etc.) don't provide a well-defined
   example local unique identifier (though note they provide an unstandardized
   `example_iri` field that might be helpful)
8. Curate an example identifier. In this case, the AgroPortal's `example_iri`
   gives enough information to pull out an example identifier.
9. Add any additional curations
