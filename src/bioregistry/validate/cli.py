"""Validation command line interface."""

from __future__ import annotations

import click

__all__ = [
    "validate",
]


@click.group()
def validate() -> None:
    """Validate data with the Bioregistry."""


@validate.command()
@click.argument("location")
@click.option("--relax", is_flag=True)
@click.option(
    "--context",
    help="The Bioregistry context, e.g., obo. If none given, uses the default Bioregistry context.",
)
@click.option(
    "--use-preferred",
    is_flag=True,
    help="If true, use preferred prefixes instead of normalized ones. If a context is given, this is disregarded.",
)
def jsonld(location: str, relax: bool, use_preferred: bool, context: str | None) -> None:
    """Validate a JSON-LD file."""
    from .utils import click_write_messages, validate_jsonld

    messages = validate_jsonld(
        location, strict=not relax, use_preferred=use_preferred, context=context
    )
    click_write_messages(messages)


@validate.command(name="ttl")
@click.argument("url")
def validate_turtle(url: str):
    """Validate prefixes in a Turtle file (either remove or local).

    For example, the Turtle file at
    https://github.com/ISE-FIZKarlsruhe/chemotion-kg/raw/4cb5c24af6494d66fb8cd849921131dbc789c163/processing/output_bfo_compliant.ttl

    @prefix nfdicore: <https://nfdi.fiz-karlsruhe.de/ontology/> .
    @prefix ns1: <http://purls.helmholtz-metadaten.de/mwo/> .
    @prefix ns2: <http://purl.obolibrary.org/obo/chebi/> .
    @prefix obo: <http://purl.obolibrary.org/obo/> .
    @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
    @prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

    https://github.com/ISE-FIZKarlsruhe/chemotion-kg/issues/2

    :return:
    """
    from .utils import click_write_messages, validate_ttl

    messages = validate_ttl(url)
    click_write_messages(messages)
