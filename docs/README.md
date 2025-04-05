# Bioregistry Documentation

This folder contains two parts:

1. [`source/`](source/) which contains the Sphinx configuration and RST files to
   create the documentation that gets deployed to ReadTheDocs at
   https://bioregistry.readthedocs.io.
2. Other documentation, which gets deployed as a static site using Jekyll and
   GitHub Pages to https://biopragmatics.github.io/bioregistry

## Build locally

The site can be deployed locally for development using Docker with the following
commands in the terminal:

```shell
git clone https://github.com/biopragmatics/bioregistry
cd bioregistry/docs
docker run --rm --volume="$PWD:/srv/jekyll" -p 4000:4000 -it jekyll/jekyll:latest jekyll serve
```
