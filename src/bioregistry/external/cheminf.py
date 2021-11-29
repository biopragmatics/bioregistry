# -*- coding: utf-8 -*-

"""Download the Chemical Information Ontology registry (children of ``CHEMINF:000464``).

To convert CHEMINF from OWL to OBO Graph JSON, do the following:

.. code-block:: sh

    $ robot convert --input cheminf.owl --format json --output cheminf.json

See the OBO Foundry workflow for preparing a docker container that has ROBOT available
"""

import json

from bioregistry.data import EXTERNAL

__all__ = [
    "get_cheminf",
]

DIRECTORY = EXTERNAL / "cheminf"
DIRECTORY.mkdir(exist_ok=True, parents=True)
PROCESSED_PATH = DIRECTORY / "processed.json"


def get_cheminf(force_download: bool = False):
    """Get the the Chemical Information Ontology registry."""
    if PROCESSED_PATH.exists() and not force_download:
        with PROCESSED_PATH.open() as file:
            return json.load(file)

    import rdflib
    from rdflib import RDFS, DC
    graph = rdflib.Graph()
    graph.load("/Users/cthoyt/.data/pyobo/raw/cheminf/2.0/cheminf.owl")
    graph.bind("rdfs", RDFS)
    graph.bind("dc", DC)
    sparql = '''\
        SELECT ?x ?label ?desc
        WHERE {
            ?x rdfs:subClassOf <http://semanticscience.org/resource/CHEMINF_000464> .
            ?x rdfs:label ?label .
            ?x dc:description ?desc
        }
    '''
    rows = graph.query(sparql)
    for uri, label, desc in rows:
        identifier = uri.toPython().split("-")[-1]
        label = label.toPython()
        desc = desc.toPython()
        print(identifier, label, desc)
    rv = {}
    # TODO provide implementation

    with PROCESSED_PATH.open("w") as file:
        json.dump(rv, file, indent=2, sort_keys=True)
    return rv


if __name__ == '__main__':
    get_cheminf(force_download=True)
