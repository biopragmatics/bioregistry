# Benchmarks

1. The [`uri_parsing`](uri_parsing) benchmark checks the `bioregistry.parse_iri`
   function. See also https://github.com/biopragmatics/bioregistry/pull/481.
2. The [`curie_parsing`](curie_parsing) benchmark checks the
   `bioregistry.parse_curie` function.
3. The [`curie_validation`](curie_validation) benchmark checks the
   `bioregistry.is_valid_curie` function.

## Overview

| URI Parsing                  | CURIE Parsing                  | CURIE Validation                  |
| ---------------------------- | ------------------------------ | --------------------------------- |
| ![](uri_parsing/results.svg) | ![](curie_parsing/results.svg) | ![](curie_validation/results.svg) |
