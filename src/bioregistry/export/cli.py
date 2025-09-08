"""Export the Bioregistry."""

import click


@click.command()
@click.pass_context
def export(ctx: click.Context) -> None:
    """Export the Bioregistry."""
    from .prefix_maps import generate_contexts
    from .rdf_export import export_rdf
    from .sssom_export import export_sssom
    from .tables_export import export_tables
    from .tsv_export import export_tsv
    from .warnings_export import export_warnings
    from .yaml_export import export_yaml

    ctx.invoke(export_warnings)
    ctx.invoke(export_rdf)
    ctx.invoke(export_tsv)
    ctx.invoke(export_yaml)
    ctx.invoke(export_sssom)
    ctx.invoke(export_tables)
    ctx.invoke(generate_contexts)


if __name__ == "__main__":
    export()
