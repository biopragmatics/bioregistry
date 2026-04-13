"""Import TIB Terminology Service collections into the corresponding Bioregistry collections."""

import click
from bioregistry.curation.nfdi.import_bartoc import import_bartoc
from bioregistry.curation.nfdi.import_tib import import_tib
from bioregistry.curation.nfdi.import_biodiv import import_biodiv


@click.command()
@click.pass_context
def main(ctx: click.Context) -> None:
    """Populate collections based on keywords from the TIB terminology service."""
    ctx.invoke(import_bartoc)
    ctx.invoke(import_tib)
    ctx.invoke(import_biodiv)


if __name__ == "__main__":
    main()
