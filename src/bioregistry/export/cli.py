# -*- coding: utf-8 -*-

"""Export the Bioregistry."""

import click

from .prefix_maps import generate_context_json_ld
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
    ctx.invoke(generate_context_json_ld)


if __name__ == "__main__":
    export()
