"""Run alignment and export."""

import click

from bioregistry.export.yaml_export import export_yaml_helper
from bioregistry.external.align import aligner_resolver


@click.command()
def main() -> None:
    """Run alignment and export."""
    for aligner_cls in aligner_resolver:
        click.secho(f"{aligner_cls.key}\n", bold=True, fg="green")
        # aligner_cls = aligner_resolver.lookup(metaprefix)
        aligner_cls.align()

        # Step 2: rasterize bioregistry export
        export_yaml_helper(output=False)


if __name__ == "__main__":
    main()
