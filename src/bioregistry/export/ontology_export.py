"""Create an OWL version of the Bioregistry."""

import datetime
import itertools as itt
import os
from pathlib import Path

import click
import requests
from funowl import (
    Annotation,
    AnnotationAssertion,
    Class,
    ClassAssertion,
    NamedIndividual,
    Ontology,
    OntologyDocument,
)
from bioregistry import manager
import bioregistry
from bioregistry.constants import ONTOLOGY_PATH
from rdflib import DCTERMS, FOAF, OWL, RDFS, Literal, Namespace, URIRef
import bioregistry.version

HERE = Path(__file__).parent.resolve()
OFN_PATH = HERE.joinpath("orcidio.ofn")
ORCIDS_PATH = HERE.joinpath("extra_orcids.txt")
ORCID = Namespace("https://orcid.org/")
OBO = Namespace("http://purl.obolibrary.org/obo/")
WIKIDATA = Namespace("http://www.wikidata.org/entity/")
BIOREGISTRY = Namespace("https://bioregistry.io/")
BIOREGISTRY_SCHEMA = Namespace("https://bioregistry.io/schema#")

URI = "https://raw.githubusercontent.com/biopragmatics/bioregistry/main/exports/ontology/bioregistry.ofn"


def main():
    """Query the Wikidata SPARQL endpoint and return JSON."""
    ontology_iri = URIRef(URI)
    charlie_iri = ORCID["0000-0003-4423-4370"]
    ontology = Ontology(iri=ontology_iri)
    ontology.annotations.extend(
        (
            Annotation(DCTERMS.title, "ORCID in OWL"),
            Annotation(DCTERMS.creator, charlie_iri),
            Annotation(DCTERMS.license, "https://creativecommons.org/publicdomain/zero/1.0/"),
            Annotation(RDFS.seeAlso, "https://github.com/biopragmatics/bioregistry"),
            Annotation(OWL.versionInfo, bioregistry.version.get_version()),
        )
    )

    parent_class = BIOREGISTRY_SCHEMA["0000001"]
    parent_class_name = "Resource"
    ontology.declarations(Class(parent_class))
    ontology.annotations.append(AnnotationAssertion(RDFS.label, parent_class, parent_class_name))

    for orcid, author in manager.read_contributors().items():
        n = ORCID[orcid]
        ontology.declarations(NamedIndividual(n))
        if author.email:
            ontology.annotations.append(AnnotationAssertion(
                FOAF.mbox,
                n,
                author.email
            ))

    for record in manager.registry.values():
        subject = BIOREGISTRY[record.prefix]
        name = record.get_name()
        description = record.get_description()

        ontology.declarations(NamedIndividual(subject))
        ontology.annotations.extend(
            [
                AnnotationAssertion(
                    RDFS.label,
                    subject,
                    name,
                    # TODO annotate source if possible
                    # [Annotation(DCTERMS.source, wikidata)],
                ),
                AnnotationAssertion(
                    RDFS.de,
                    subject,
                    name,
                    # TODO annotate source if possible
                    # [Annotation(DCTERMS.source, wikidata)],
                ),
                ClassAssertion(parent_class, subject),
            ]
        )
        # if description:
        #     ontology.annotations.append(
        #         AnnotationAssertion(
        #             DCTERMS.description,
        #             subject,
        #             description,
        #         )
        #     )

    doc = OntologyDocument(
        ontology=ontology,
        orcid=ORCID,
        wikidata=WIKIDATA,
        obo=OBO,
        dcterms=DCTERMS,
        bioregistry=BIOREGISTRY,
        owl=OWL,
        **{
            "bioregistry.schema": BIOREGISTRY_SCHEMA
        },
    )
    click.echo(f"writing to {ONTOLOGY_PATH}")
    ONTOLOGY_PATH.write_text(f"{doc}\n")


if __name__ == "__main__":
    main()
