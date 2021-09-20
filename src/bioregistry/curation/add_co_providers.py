# -*- coding: utf-8 -*-

"""Add providers for Crop Ontology entries."""

import requests

import bioregistry


def main():
    """Run the script."""
    r = dict(bioregistry.read_registry())
    for prefix, resource in r.items():
        if not prefix.startswith("co_"):
            continue
        if not resource.example:
            print(prefix, "missing example")
            continue
        if resource.url:
            print(prefix, "has url", resource.url)
            url = bioregistry.get_iri(prefix, resource.example)
            res = requests.get(url)
            print(res.text)
            print()
            continue
        resource.url = f"https://www.cropontology.org/rdf/{prefix.upper()}:$1"
    bioregistry.write_registry(r)


if __name__ == "__main__":
    main()
