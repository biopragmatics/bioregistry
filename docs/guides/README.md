# Curation Guides

This folder contains various task-specific curation guides.

- [Curating new providers](/curation/providers)

## How to add new guides

1. Create a new markdown file in this directory (`bioregistry/docs/guides/`)
2. Use appropriate front-matter so that Jekyll can give it a permalink
   (see
   [here](https://github.com/biopragmatics/bioregistry/blob/fe2a685503ae2c9ff863908bf885c71fd240c21d/docs/guides/providers.md?plain=1#L1-L5)
   for an example)
3. Add it to the list above

## What makes a good guide

A good guide is able to educate and guide a curator through a new scenario.

As a guide writer, you should assume a small amount of background knowledge on the Bioregistry
and using GitHub, but effectively none about the internal structure of the Bioregistry repository
nor its data schema.

Your guide should do the following:

1. Give some high-level motivation on what curation from your guide accomplishes
2. Explain in what files curation should be done. Give links to that file on the GitHub main branch for the
   repository, so they can navigate in the web browser and see it. 
3. Explain how to do the curation 
   - Give a step-by-step guide
   - Illustrate your guide with screenshots, code blocks (with highlighting), 
     permalinks to files or sections of files in the Bioregistry GitHub repository
