# -*- coding: utf-8 -*-

"""Export the Bioregistry."""

import click

from .rdf_export import export_rdf
from .tsv_export import export_tsv
from .yaml_export import export_yaml


@click.command()
@click.pass_context
def export(ctx: click.Context):
    """Export the Bioregistry."""
    ctx.invoke(export_rdf)
    ctx.invoke(export_tsv)
    ctx.invoke(export_yaml)


if __name__ == '__main__':
    export()
